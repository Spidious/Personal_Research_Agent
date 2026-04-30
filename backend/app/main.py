from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine
from .models import tables  # noqa: F401 — ensures models are registered
from .routers import briefings, health, topics


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Table creation handled by init SQL; this is a no-op safety net for dev
    yield
    await engine.dispose()


app = FastAPI(title="Personal Research Agent", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(topics.router)
app.include_router(briefings.router)
