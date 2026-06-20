# Run Compose - Lab 05 Camera Stream

## 1. Prepare environment

```bash
cp .env.example .env
```

PowerShell:

```powershell
Copy-Item .env.example .env
```

## 2. Start stack

```bash
docker compose up -d --build
```

The stack starts:

- `api`: Camera Stream on `http://localhost:8000`
- `db`: PostgreSQL readiness dependency
- `ai-service`: mock AI Vision on `http://localhost:9000`
- `analytics-mock`: mock Analytics on `http://localhost:9010`

## 3. Check readiness

```bash
curl http://localhost:8000/health
curl http://localhost:9000/health
curl http://localhost:9010/health
docker compose ps
```

## 4. Run an end-to-end request

```bash
curl -X POST http://localhost:8000/api/v1/frames \
  -H "Authorization: Bearer local-dev-token" \
  -H "Content-Type: application/json" \
  -d '{"camera_id":"CAM-A01","location":"Main lobby","frame_format":"jpeg","image_base64":"dGVzdC1pbWFnZS1mcmFtZQ==","captured_at":"2026-05-13T08:30:00+07:00","motion_score":0.82}'
```

Then analyze the returned `frame_id`:

```bash
curl -X POST http://localhost:8000/api/v1/frames/FR-YYYYMMDD-0001/analyze \
  -H "Authorization: Bearer local-dev-token"
```

During analyze, the API sends AI Vision a payload with `request_id`, `camera_id`, `timestamp`, `location`, `motion_score`, and `image_base64`, then sends Analytics an event with `risk_level`, `unknown_person`, and `alert_candidate`.

## 5. Run Newman

```bash
npm install
npm run test:compose
```

## 6. Stop stack

```bash
docker compose down
```
