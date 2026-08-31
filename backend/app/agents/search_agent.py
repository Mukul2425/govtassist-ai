"""Scheme search with metadata filtering and keyword matching."""

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.logging_config import get_logger
from app.models.scheme import Scheme
from app.schemas.profile import UserProfile

logger = get_logger(__name__)


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

    if query:
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

    logger.info("scheme_search_complete", count=len(schemes), state=profile.state)
    return schemes
