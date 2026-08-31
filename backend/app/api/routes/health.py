from fastapi import APIRouter

from app.config import get_settings
from app.services.llm_service import llm_service

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/health")
async def health_check() -> dict:
    return {
        "status": "healthy",
        "app": settings.app_name,
        "environment": settings.app_env,
        "llm_available": llm_service.is_available,
        "llm_mock_mode": settings.llm_mock_mode,
    }
