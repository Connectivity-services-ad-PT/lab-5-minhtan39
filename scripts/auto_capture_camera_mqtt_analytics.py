import base64
import json
import os
import time
import urllib.request
from datetime import datetime, timezone
from uuid import uuid4

import paho.mqtt.client as mqtt

CAMERA_URL = "https://camera.labaiotdnu.app/video?key=matkhau_cua_ban"

API_URL = "http://localhost:8000/api/v1/frames"
ANALYZE_URL_TEMPLATE = "http://localhost:8000/api/v1/frames/{frame_id}/analyze"
TOKEN = "local-dev-token"

OUTPUT_PATH = r"data\camera\auto-camera-frame.jpg"

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
CAMERA_EVENT_TOPIC = os.getenv("CAMERA_EVENT_TOPIC", "smart-campus/events/camera")


def capture_mjpeg_frame(url: str, output_path: str) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print("[1] Dang ket noi camera live...")

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
            "Accept": "multipart/x-mixed-replace,image/jpeg,image/*,*/*",
            "Referer": "https://camera.labaiotdnu.app/",
        },
    )

    response = urllib.request.urlopen(request, timeout=15)

    buffer = b""
    start_time = time.time()

    while time.time() - start_time < 15:
        chunk = response.read(4096)
        if not chunk:
            continue

        buffer += chunk

        start = buffer.find(b"\xff\xd8")
        end = buffer.find(b"\xff\xd9")

        if start != -1 and end != -1 and end > start:
            jpg = buffer[start:end + 2]

            with open(output_path, "wb") as f:
                f.write(jpg)

            print(f"[OK] Da tu dong lay frame: {output_path}")
            return output_path

    raise RuntimeError("Khong lay duoc frame tu camera live trong 15 giay.")


def post_json(url: str, payload: dict, token: str | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read().decode("utf-8")
        return json.loads(body)


def publish_to_analytics(event: dict):
    print("[4] Publish event sang Analytics qua MQTT...")
    print(f"MQTT_HOST={MQTT_HOST}")
    print(f"MQTT_PORT={MQTT_PORT}")
    print(f"TOPIC={CAMERA_EVENT_TOPIC}")

    client = mqtt.Client()
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()

    payload = json.dumps(event, ensure_ascii=False)
    result = client.publish(CAMERA_EVENT_TOPIC, payload, qos=1)
    result.wait_for_publish()

    client.loop_stop()
    client.disconnect()

    print("[OK] Da publish event sang Analytics.")
    print(json.dumps(event, indent=2, ensure_ascii=False))


def main():
    captured_at = datetime.now(timezone.utc).isoformat()

    image_path = capture_mjpeg_frame(CAMERA_URL, OUTPUT_PATH)

    with open(image_path, "rb") as f:
        image_base64 = base64.b64encode(f.read()).decode("utf-8")

    motion_score = 0.82

    frame_payload = {
        "camera_id": "CAM-A01",
        "location": "Live Camera LabAIoT DNU",
        "frame_format": "jpeg",
        "image_base64": image_base64,
        "captured_at": captured_at,
        "motion_score": motion_score,
    }

    print("[2] Gui frame vao Camera API...")
    frame_response = post_json(API_URL, frame_payload, TOKEN)
    print(json.dumps(frame_response, indent=2, ensure_ascii=False))

    frame_id = frame_response["frame_id"]
    motion_level = frame_response.get("motion_level", "unknown")

    print("[3] Goi analyze de gui sang Vision Mock...")
    analyze_url = ANALYZE_URL_TEMPLATE.format(frame_id=frame_id)
    analyze_response = post_json(analyze_url, {}, TOKEN)
    print(json.dumps(analyze_response, indent=2, ensure_ascii=False))

    vision_body = analyze_response.get("vision", {}).get("body", {})
    detections = vision_body.get("detections", [])

    unknown_person = vision_body.get("unknown_person")
    if unknown_person is None:
        unknown_person = any(d.get("label") == "person" for d in detections)

    risk_level = vision_body.get("risk_level")
    if risk_level is None:
        risk_level = "high" if unknown_person else "low"

    alert_candidate = risk_level in ["high", "critical"] or unknown_person is True

    camera_event = {
        "event_id": f"cam-{uuid4()}",
        "event_type": "camera.motion.analyzed",
        "source_service": "team-camera",
        "request_id": f"vision-{frame_id}",
        "frame_id": frame_id,
        "camera_id": "CAM-A01",
        "location": "Live Camera LabAIoT DNU",
        "snapshot_url": f"local://{OUTPUT_PATH.replace(os.sep, '/')}",
        "motion_detected": True,
        "motion_score": motion_score,
        "motion_level": motion_level,
        "risk_level": risk_level,
        "unknown_person": unknown_person,
        "alert_candidate": alert_candidate,
        "detections": detections,
        "timestamp": captured_at,
    }

    publish_to_analytics(camera_event)

    print("[DONE] Full flow thanh cong: Camera -> Vision Mock -> Analytics MQTT.")


if __name__ == "__main__":
    main()
