# Lab 05 Readiness Checklist - Camera Stream

- [x] API container exposes `8000:8000` and responds to `GET /health`.
- [x] PostgreSQL has a `pg_isready` healthcheck.
- [x] AI Vision mock has `GET /health` and `POST /api/v1/detect`.
- [x] Analytics mock has `GET /health` and `POST /api/v1/events`.
- [x] API reads `VISION_SERVICE_URL`, `ANALYTICS_URL`, `AUTH_TOKEN`, and timeout from `.env`.
- [x] All services share `team-internal`; API also joins `class-net` for class demo compatibility.
- [x] API image runs as non-root user through the Dockerfile inherited from Lab 04.
- [x] Newman script targets the Camera Stream collection and local environment.
