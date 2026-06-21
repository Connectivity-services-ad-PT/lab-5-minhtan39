# AI Vision integration handoff - Team Camera Stream

Tai lieu nay de ban trong nhom clone repo ve lam tiep phan ket noi AI Vision that.

## Folder chinh de chay

```powershell
cd C:\Projects\Bailap-dich_Vu_Ket_Noi\lab-5-minhtan39
```

Neu clone tu GitHub ve may khac:

```powershell
git clone https://github.com/Connectivity-services-ad-PT/lab-5-minhtan39.git
cd lab-5-minhtan39
```

## Chay stack demo hien tai

```powershell
docker compose up -d --build
docker compose ps
curl http://localhost:8000/health
```

Stack hien tai gom:

- Camera API: `http://localhost:8000`
- AI Vision mock: `http://localhost:9000`
- Analytics mock: `http://localhost:9010`
- PostgreSQL database

## Noi AI Vision that vao dau?

Camera API doc URL Vision tu bien moi truong `VISION_SERVICE_URL`.

Trong `docker-compose.yml`, doi gia tri nay ve URL cua service Vision that:

```yaml
VISION_SERVICE_URL: http://<vision-host>:<vision-port>
```

Vision that can expose endpoint:

```http
POST /api/v1/detect
Content-Type: application/json
```

## Payload Camera gui sang Vision

Camera Stream se gui request co dang:

```json
{
  "request_id": "vision-FR-20260620-0001",
  "camera_id": "CAM-A01",
  "timestamp": "2026-06-20T08:30:00+07:00",
  "location": "Main lobby",
  "motion_score": 0.82,
  "image_base64": "<jpeg-base64>",
  "snapshot_url": null
}
```

Quan trong:

- `image_base64` la anh JPEG/PNG da ma hoa base64.
- `camera_id` phai theo format contract, vi du `CAM-A01`.
- `motion_score` nam tu `0` den `1`.
- `request_id` dung de doi soat log giua Camera va Vision.

## Response Vision can tra ve

```json
{
  "request_id": "vision-FR-20260620-0001",
  "camera_id": "CAM-A01",
  "timestamp": "2026-06-20T08:30:01+07:00",
  "detections": [
    {
      "label": "person",
      "confidence": 0.92,
      "bbox": { "x": 120, "y": 80, "width": 210, "height": 430 }
    }
  ],
  "unknown_person": true,
  "risk_level": "high"
}
```

Camera Stream se lay response nay de tao event `camera.motion.analyzed`.

## Gui event sang Analytics

Script full flow:

```powershell
python scripts\auto_capture_camera_mqtt_analytics.py
```

Neu Analytics dung MQTT that, cau hinh:

```powershell
$env:MQTT_HOST="<analytics-mqtt-host>"
$env:MQTT_PORT="1883"
$env:CAMERA_EVENT_TOPIC="smart-campus/events/camera"
python scripts\auto_capture_camera_mqtt_analytics.py
```

Event gui sang Analytics co dang:

```json
{
  "event_type": "camera.motion.analyzed",
  "source_service": "team-camera",
  "frame_id": "FR-20260620-0001",
  "camera_id": "CAM-A01",
  "location": "Live Camera LabAIoT DNU",
  "motion_detected": true,
  "motion_score": 0.82,
  "motion_level": "high",
  "risk_level": "high",
  "unknown_person": true,
  "alert_candidate": true
}
```

Analytics chi can event nay de aggregate KPI, khong can nhan `image_base64`.

## Evidence da co

Trong thu muc `reports/` co:

- `newman-lab05-compose.html`
- `newman-lab05-compose.xml`
- `docker-compose-ps.png`
- `health-api.png`
- `camera-live-source.png`
- `analyze-live-frame-response.png`
- `Bao_cao_BTL_Camera_Stream_Service.docx`

Khong dung `reports/logs-compose.txt` lam evidence chinh vi file log nay co the chua log cu tu lan chay truoc.
