import os
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


SERVICE_NAME = os.getenv("SERVICE_NAME", "camera-stream")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "0.5.0-team-camera")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "local-dev-token")
VISION_SERVICE_URL = os.getenv("VISION_SERVICE_URL", "http://ai-service:9000")
ANALYTICS_URL = os.getenv("ANALYTICS_URL", "http://analytics-mock:9010")
UPSTREAM_TIMEOUT_SECONDS = float(os.getenv("UPSTREAM_TIMEOUT_SECONDS", "3.0"))

app = FastAPI(title="FIT4110 Lab 05 - Camera Stream Service", version=SERVICE_VERSION)


class FrameFormat(str, Enum):
    jpeg = "jpeg"
    png = "png"


class MotionLevel(str, Enum):
    none = "none"
    low = "low"
    medium = "medium"
    high = "high"


class FrameCreate(BaseModel):
    camera_id: str = Field(..., min_length=3, examples=["CAM-A01"])
    location: str = Field(..., min_length=2, examples=["Main lobby"])
    frame_format: FrameFormat = FrameFormat.jpeg
    image_base64: str = Field(..., min_length=16, max_length=500000)
    captured_at: str = Field(..., examples=["2026-05-13T08:30:00+07:00"])
    motion_score: float = Field(..., ge=0, le=1, examples=[0.82])


FRAMES: List[Dict] = []


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def next_frame_id() -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"FR-{today}-{len(FRAMES) + 1:04d}"


def motion_level(score: float) -> str:
    if score >= 0.75:
        return MotionLevel.high.value
    if score >= 0.4:
        return MotionLevel.medium.value
    if score > 0:
        return MotionLevel.low.value
    return MotionLevel.none.value


def build_vision_payload(frame_id: str, frame: Dict) -> Dict:
    return {
        "request_id": f"vision-{frame_id}",
        "camera_id": frame["camera_id"],
        "timestamp": frame["captured_at"],
        "location": frame["location"],
        "motion_score": frame["motion_score"],
        "image_base64": frame["image_base64"],
        "snapshot_url": None,
    }


def build_camera_event(frame_id: str, frame: Dict, vision_body: Dict) -> Dict:
    risk_level = vision_body.get("risk_level", "low") if isinstance(vision_body, dict) else "low"
    unknown_person = bool(vision_body.get("unknown_person", False)) if isinstance(vision_body, dict) else False
    return {
        "event_type": "camera.motion.analyzed",
        "source_service": "team-camera",
        "request_id": f"vision-{frame_id}",
        "frame_id": frame_id,
        "camera_id": frame["camera_id"],
        "location": frame["location"],
        "occurred_at": now_iso(),
        "timestamp": frame["captured_at"],
        "motion_detected": True,
        "motion_score": frame["motion_score"],
        "motion_level": frame["motion_level"],
        "risk_level": risk_level,
        "unknown_person": unknown_person,
        "alert_candidate": risk_level in {"high", "critical"} or unknown_person,
    }


def problem(status_code: int, title: str, detail: str, instance: Optional[str] = None) -> Dict:
    return {"type": "about:blank", "title": title, "status": status_code, "detail": detail, "instance": instance}


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    body = exc.detail if isinstance(exc.detail, dict) else problem(exc.status_code, "HTTP error", str(exc.detail), str(request.url.path))
    return JSONResponse(
        status_code=exc.status_code,
        content=body,
        media_type="application/problem+json",
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    first = exc.errors()[0] if exc.errors() else {}
    return JSONResponse(
        status_code=422,
        content=problem(422, "Validation error", first.get("msg", "invalid request"), str(request.url.path)),
        media_type="application/problem+json",
    )


def verify_bearer_token(authorization: Optional[str] = Header(default=None)) -> None:
    if authorization != f"Bearer {AUTH_TOKEN}":
        raise HTTPException(401, problem(401, "Unauthorized", "Missing or invalid bearer token"))


async def post_with_timeout(url: str, payload: Dict) -> Dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=UPSTREAM_TIMEOUT_SECONDS) as response:
            body = response.read().decode("utf-8")
            return {"ok": True, "status": response.status, "body": json.loads(body) if body else {}}
    except TimeoutError:
        raise HTTPException(503, problem(503, "Dependency timeout", f"Timeout calling {url}"))
    except urllib.error.HTTPError as exc:
        raise HTTPException(502, problem(502, "Dependency error", f"{url} returned {exc.code}"))
    except urllib.error.URLError:
        raise HTTPException(503, problem(503, "Dependency unavailable", f"Cannot connect to {url}"))


@app.get("/health")
def health() -> Dict:
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "dependencies": {"vision": VISION_SERVICE_URL, "analytics": ANALYTICS_URL},
    }


@app.post("/api/v1/frames", status_code=201, dependencies=[Depends(verify_bearer_token)])
async def upload_frame(payload: FrameCreate) -> Dict:
    frame_id = next_frame_id()
    row = payload.model_dump()
    row.update({"frame_id": frame_id, "created_at": now_iso(), "motion_level": motion_level(payload.motion_score)})
    FRAMES.append(row)
    return {"frame_id": frame_id, "camera_id": payload.camera_id, "accepted": True, "motion_level": row["motion_level"], "created_at": row["created_at"]}


@app.post("/api/v1/frames/{frame_id}/analyze", dependencies=[Depends(verify_bearer_token)])
async def analyze_frame(frame_id: str) -> Dict:
    frame = next((item for item in FRAMES if item["frame_id"] == frame_id), None)
    if frame is None:
        raise HTTPException(404, problem(404, "Not found", f"Frame {frame_id} does not exist"))

    vision_payload = build_vision_payload(frame_id, frame)
    vision = await post_with_timeout(
        f"{VISION_SERVICE_URL.rstrip('/')}/api/v1/detect",
        vision_payload,
    )
    vision_body = vision.get("body", {}) if isinstance(vision, dict) else {}
    analytics_event = build_camera_event(frame_id, frame, vision_body)
    analytics = await post_with_timeout(
        f"{ANALYTICS_URL.rstrip('/')}/api/v1/events",
        analytics_event,
    )
    return {
        "frame_id": frame_id,
        "vision_request": vision_payload,
        "vision": vision_body or vision,
        "analytics_event": analytics_event,
        "analytics": analytics,
    }


@app.get("/api/v1/frames", dependencies=[Depends(verify_bearer_token)])
def list_frames(camera_id: Optional[str] = Query(default=None), limit: int = Query(default=20, ge=1, le=100)) -> Dict:
    items = FRAMES
    if camera_id:
        items = [item for item in items if item["camera_id"] == camera_id]
    return {"items": items[-limit:]}


@app.get("/api/v1/frames/{frame_id}", dependencies=[Depends(verify_bearer_token)])
def get_frame(frame_id: str) -> Dict:
    frame = next((item for item in FRAMES if item["frame_id"] == frame_id), None)
    if frame is None:
        raise HTTPException(404, problem(404, "Not found", f"Frame {frame_id} does not exist"))
    return frame
