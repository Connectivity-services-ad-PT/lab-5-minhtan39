import base64
import json
import os
import time
import urllib.request
from datetime import datetime, timezone

CAMERA_URL = "https://camera.labaiotdnu.app/video?key=matkhau_cua_ban"
API_URL = "http://localhost:8000/api/v1/frames"
ANALYZE_URL_TEMPLATE = "http://localhost:8000/api/v1/frames/{frame_id}/analyze"
TOKEN = "local-dev-token"

OUTPUT_PATH = r"data\camera\auto-camera-frame.jpg"


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

    with urllib.request.urlopen(request, timeout=15) as response:
        body = response.read().decode("utf-8")
        return json.loads(body)


def main():
    image_path = capture_mjpeg_frame(CAMERA_URL, OUTPUT_PATH)

    with open(image_path, "rb") as f:
        image_base64 = base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "camera_id": "CAM-A01",
        "location": "Live Camera LabAIoT DNU",
        "frame_format": "jpeg",
        "image_base64": image_base64,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "motion_score": 0.80,
    }

    print("[2] Gui frame vao Camera API...")
    frame_response = post_json(API_URL, payload, TOKEN)
    print(json.dumps(frame_response, indent=2, ensure_ascii=False))

    frame_id = frame_response["frame_id"]

    print("[3] Goi analyze de gui sang Vision Mock...")
    analyze_url = ANALYZE_URL_TEMPLATE.format(frame_id=frame_id)
    analyze_response = post_json(analyze_url, {}, TOKEN)
    print(json.dumps(analyze_response, indent=2, ensure_ascii=False))

    print("[DONE] Demo tu dong hoan tat.")


if __name__ == "__main__":
    main()