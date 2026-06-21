import json
import os
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

MQTT_HOST = os.getenv("MQTT_HOST", "26.109.160.213")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC = os.getenv("CAMERA_EVENT_TOPIC", "smart-campus/events/camera")

event = {
    "event_id": "cam-FR-DEMO-001",
    "request_id": "vision-FR-DEMO-001",
    "event_type": "camera.motion.analyzed",
    "source_service": "team-camera",

    "frame_id": "FR-DEMO-001",
    "camera_id": "CAM-A01",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "location": "Live Camera LabAIoT DNU",

    "motion_detected": True,
    "motion_score": 0.82,
    "motion_level": "high",

    "snapshot_url": "local://data/camera/auto-camera-frame.jpg",

    "risk_level": "high",
    "unknown_person": True,
    "alert_candidate": True,

    "detections": [
        {
            "label": "person",
            "confidence": 0.94
        },
        {
            "label": "backpack",
            "confidence": 0.81
        }
    ]
}

print("[1] Connecting MQTT...")
print("MQTT_HOST =", MQTT_HOST)
print("MQTT_PORT =", MQTT_PORT)
print("TOPIC =", TOPIC)

client = mqtt.Client()
client.connect(MQTT_HOST, MQTT_PORT, 60)
client.loop_start()

payload = json.dumps(event, ensure_ascii=False)
result = client.publish(TOPIC, payload, qos=1)
result.wait_for_publish()

client.loop_stop()
client.disconnect()

print("[OK] Da gui event dung nghiep vu sang Analytics")
print(json.dumps(event, indent=2, ensure_ascii=False))
