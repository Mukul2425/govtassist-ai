"""Improved scheme search with profile-aware relevance boosting."""

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.logging_config import get_logger
from app.models.scheme import Scheme
from app.schemas.profile import UserProfile

logger = get_logger(__name__)

PROFILE_CATEGORY_MAP: dict[str, list[str]] = {
    "farmer": ["Agriculture", "Micro Finance"],
    "student": ["Education", "Skill Development"],
    "unemployed": ["Employment", "Skill Development", "Education"],
    "self_employed": ["Entrepreneurship", "Micro Finance", "Skill Development"],
    "business": ["Entrepreneurship", "Micro Finance"],
    "laborer": ["Social Security", "Skill Development", "Insurance"],
}


def _profile_keywords(profile: UserProfile) -> list[str]:
    keywords: list[str] = []
    ctx = profile.to_rule_context()
    if occupation := ctx.get("occupation"):
        keywords.append(str(occupation))
        keywords.extend(PROFILE_CATEGORY_MAP.get(str(occupation), []))
    if education := ctx.get("education"):
        keywords.append(str(education))
    if caste := ctx.get("caste_category"):
        keywords.append(str(caste))
    if ctx.get("is_woman") or ctx.get("gender") == "female":
        keywords.extend(["women", "woman", "female"])
    if ctx.get("is_bpl"):
        keywords.append("bpl")
    return [k.lower() for k in keywords]


async def search_schemes(
    session: AsyncSession,
    profile: UserProfile,
    query: str | None = None,
    limit: int = 50,
) -> list[Scheme]:
    stmt = (
        select(Scheme)
        .options(selectinload(Scheme.eligibility_rules))
        .where(Scheme.is_active.is_(True))
    )

    if profile.state:
        stmt = stmt.where(
            or_(
                Scheme.applicable_states.contains(["All India"]),
                Scheme.applicable_states.contains([profile.state]),
                func.array_length(Scheme.applicable_states, 1).is_(None),
            )
        )

    if query and len(query.split()) <= 4:
        search_term = f"%{query.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Scheme.name).like(search_term),
                func.lower(Scheme.short_description).like(search_term),
                func.lower(Scheme.category).like(search_term),
                Scheme.keywords.any(query.lower()),
            )
        )

    stmt = stmt.order_by(Scheme.name).limit(limit)
    result = await session.execute(stmt)
    schemes = list(result.scalars().unique().all())

    # Profile-aware re-ranking: boost schemes matching occupation/category
    pkeywords = _profile_keywords(profile)
    if pkeywords:
        def relevance(scheme: Scheme) -> int:
            score = 0
            cat = scheme.category.lower()
            kws = [k.lower() for k in scheme.keywords]
            for pk in pkeywords:
                if pk in cat or any(pk in kw for kw in kws):
                    score += 2
                if pk in scheme.name.lower() or pk in scheme.short_description.lower():
                    score += 1
            return score

        schemes.sort(key=relevance, reverse=True)

    logger.info("scheme_search_complete", count=len(schemes), state=profile.state)
    return schemes
