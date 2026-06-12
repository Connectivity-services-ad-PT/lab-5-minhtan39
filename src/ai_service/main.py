from typing import List

from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(title="Mock AI Vision Service", version="0.5.0-team-camera")


class Detection(BaseModel):
    label: str
    confidence: float


class DetectRequest(BaseModel):
    frame_id: str
    camera_id: str
    image_base64: str


class DetectResponse(BaseModel):
    frame_id: str
    model_version: str
    detections: List[Detection]


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "ai-vision-mock", "version": "0.5.0-team-camera"}


@app.post("/api/v1/detect", response_model=DetectResponse)
def detect(payload: DetectRequest) -> DetectResponse:
    return DetectResponse(
        frame_id=payload.frame_id,
        model_version="mock-yolov8n-0.1",
        detections=[
            Detection(label="person", confidence=0.94),
            Detection(label="backpack", confidence=0.81),
        ],
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9000)
