from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(title="Mock Analytics Service", version="0.5.0-team-camera")


class EventIn(BaseModel):
    event_type: str
    frame_id: str
    camera_id: str
    occurred_at: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "analytics-mock", "version": "0.5.0-team-camera"}


@app.post("/api/v1/events", status_code=202)
def accept_event(payload: EventIn) -> dict:
    return {"accepted": True, "event_type": payload.event_type, "frame_id": payload.frame_id}
