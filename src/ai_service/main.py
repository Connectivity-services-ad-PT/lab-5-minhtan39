from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(title="Mock AI Vision Service", version="0.5.0-team-camera")


class BoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int


class Detection(BaseModel):
    label: str
    confidence: float
    bbox: Optional[BoundingBox] = None


class DetectRequest(BaseModel):
    request_id: str
    camera_id: str
    timestamp: str
    location: str
    motion_score: float
    image_base64: str
    snapshot_url: Optional[str] = None


class DetectResponse(BaseModel):
    request_id: str
    camera_id: str
    timestamp: str
    model_version: str
    detections: List[Detection]
    unknown_person: bool
    risk_level: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "ai-vision-mock", "version": "0.5.0-team-camera"}


@app.post("/api/v1/detect", response_model=DetectResponse)
def detect(payload: DetectRequest) -> DetectResponse:
    risk_level = "high" if payload.motion_score >= 0.75 else "warning"
    return DetectResponse(
        request_id=payload.request_id,
        camera_id=payload.camera_id,
        timestamp=payload.timestamp,
        model_version="mock-yolov8n-0.1",
        detections=[
            Detection(label="person", confidence=0.94, bbox=BoundingBox(x=120, y=80, width=210, height=430)),
            Detection(label="backpack", confidence=0.81, bbox=BoundingBox(x=260, y=210, width=80, height=120)),
        ],
        unknown_person=True,
        risk_level=risk_level,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9000)
