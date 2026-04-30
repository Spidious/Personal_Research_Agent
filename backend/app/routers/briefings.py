"""API routes for triggering briefing pipeline runs."""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, EmailStr

from ..agent.pipeline import run_pipeline

router = APIRouter(prefix="/briefings", tags=["briefings"])


class RunRequest(BaseModel):
    to_email: str
    topic_name: str | None = None


@router.post("/run")
async def trigger_briefing(body: RunRequest, background_tasks: BackgroundTasks):
    """Trigger a pipeline run. Runs in the background so the HTTP call returns fast."""
    background_tasks.add_task(run_pipeline, to_email=body.to_email, topic_name=body.topic_name)
    return {"status": "queued", "to": body.to_email, "topic": body.topic_name}
