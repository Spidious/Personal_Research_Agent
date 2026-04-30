"""Health check endpoints for liveness and database connectivity probes."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    """Basic liveness probe — returns 200 as long as the process is running."""
    return {"status": "ok"}


@router.get("/health/db")
async def health_db(db: AsyncSession = Depends(get_db)):
    """Readiness probe that verifies the database connection is reachable."""
    await db.execute(text("SELECT 1"))
    return {"status": "ok", "db": "connected"}
