from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, health, recommendations, schemes
from app.config import get_settings
from app.logging_config import get_logger
from app.models.database import Base, engine

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("application_started", env=settings.app_env)
    yield
    await engine.dispose()
    logger.info("application_shutdown")


app = FastAPI(
    title=settings.app_name,
    description=(
        "AI-Powered Government Scheme Discovery & Eligibility Assistant. "
        "Combines LLM profile extraction, deterministic rules engine, and RAG "
        "for personalized scheme recommendations."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(schemes.router, prefix=settings.api_prefix)
app.include_router(recommendations.router, prefix=settings.api_prefix)
app.include_router(admin.router, prefix=settings.api_prefix)


@app.get("/")
async def root() -> dict:
    return {
        "message": "Welcome to GovtAssist AI",
        "docs": "/docs",
        "api": settings.api_prefix,
    }
