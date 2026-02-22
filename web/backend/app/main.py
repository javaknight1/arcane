from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import get_engine
from .routers.auth import router as auth_router
from .routers.generation import router as generation_router
from .routers.health import router as health_router
from .routers.projects import router as projects_router
from .routers.roadmaps import router as roadmaps_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await get_engine().dispose()


app = FastAPI(
    title="Arcane",
    description="AI-powered roadmap generator API",
    version="0.1.0",
    lifespan=lifespan,
)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(projects_router, prefix="/projects", tags=["projects"])
app.include_router(roadmaps_router, tags=["roadmaps"])
app.include_router(generation_router, tags=["generation"])
