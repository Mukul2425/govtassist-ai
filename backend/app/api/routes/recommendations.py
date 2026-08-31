from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import orchestrator
from app.agents.profile_agent import extract_profile
from app.models.database import get_db
from app.schemas.profile import ProfileExtractionRequest, ProfileExtractionResponse
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.post("/extract-profile", response_model=ProfileExtractionResponse)
async def extract_user_profile(
    request: ProfileExtractionRequest,
) -> ProfileExtractionResponse:
    return await extract_profile(request.query)


@router.post("", response_model=RecommendationResponse)
async def get_recommendations(
    request: RecommendationRequest,
    db: AsyncSession = Depends(get_db),
) -> RecommendationResponse:
    return await orchestrator.run(
        session=db,
        query=request.query,
        profile=request.profile,
        max_results=request.max_results,
    )
