"""API routes for creating and listing user topics."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.tables import Topic, User

router = APIRouter(prefix="/topics", tags=["topics"])


class TopicCreate(BaseModel):
    user_email: str
    name: str
    description: str = ""


class TopicOut(BaseModel):
    id: int
    name: str
    description: str

    model_config = {"from_attributes": True}


@router.get("/{user_email}", response_model=list[TopicOut]) # todo: Require authentication to access user details
async def list_topics(user_email: str, db: AsyncSession = Depends(get_db)):
    """Return all topics belonging to the given user email."""
    result = await db.execute(
        select(Topic).join(User).where(User.email == user_email)
    )
    return result.scalars().all()


@router.post("/", response_model=TopicOut, status_code=201) # todo: Consider changing to /new-topic
async def create_topic(body: TopicCreate, db: AsyncSession = Depends(get_db)):
    """Create a topic for a user, creating the user row first if it does not exist."""
    result = await db.execute(select(User).where(User.email == body.user_email))
    user = result.scalar_one_or_none()
    if not user:
        user = User(email=body.user_email)
        db.add(user)
        await db.flush()

    topic = Topic(user_id=user.id, name=body.name, description=body.description)
    db.add(topic)
    await db.commit()
    await db.refresh(topic)
    return topic
