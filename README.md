# FIT4110 Lab 05 - Camera Stream Compose Readiness

This repository submits Lab 05 for `team-camera`.

## Compose Stack

```text
api             Camera Stream API on port 8000
db              PostgreSQL readiness dependency
ai-service      Mock AI Vision service on port 9000
analytics-mock  Mock Analytics service on port 9010
```

## Main Files

```text
docker-compose.yml
Dockerfile
.env.example
RUN_COMPOSE.md
src/camera_app/main.py
src/ai_service/main.py
src/analytics_mock/main.py
contracts/camera-stream.openapi.yaml
docs/BUSINESS_ANALYSIS_CAMERA.md
postman/collections/FIT4110_lab05_camera_compose.postman_collection.json
checklists/readiness-checklist.md
```

## Run

```bash
docker compose up -d --build
curl http://localhost:8000/health
curl http://localhost:9000/health
curl http://localhost:9010/health
npm run test:compose
```

Stop:

```bash
docker compose down
```

## Buoi 6 Readiness

- API binds to `0.0.0.0`.
- API publishes `8000:8000`.
- Dependency URLs live in `.env.example`.
- AI Vision and Analytics mocks allow an end-to-end local demo.
- Dependency timeout/error behavior returns controlled Problem Details responses.
- Compose demo follows the 7-service business flow: upload a motion frame, send base64 snapshot metadata to AI Vision, receive `risk_level/unknown_person`, and emit an Analytics event.
