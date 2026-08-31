"""Profile understanding agent."""

from app.logging_config import get_logger
from app.schemas.profile import ProfileExtractionResponse, UserProfile
from app.services.llm_service import llm_service

logger = get_logger(__name__)


async def extract_profile(query: str, existing_profile: UserProfile | None = None) -> ProfileExtractionResponse:
    profile, confidence, notes = await llm_service.extract_profile(query)

    if existing_profile:
        merged = existing_profile.model_dump()
        new_data = profile.model_dump(exclude_none=True)
        merged.update({k: v for k, v in new_data.items() if v is not None})
        profile = UserProfile.model_validate(merged)
        notes.append("Merged with existing profile data")

    logger.info(
        "profile_extracted",
        fields=list(profile.model_dump(exclude_none=True).keys()),
        confidence=confidence,
    )

    return ProfileExtractionResponse(
        profile=profile,
        confidence=confidence,
        extraction_notes=notes,
    )
