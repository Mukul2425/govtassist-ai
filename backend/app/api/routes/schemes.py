from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.database import get_db
from app.models.scheme import Scheme
from app.schemas.scheme import SchemeDetail, SchemeListResponse, SchemeSummary
from app.services.cache_service import cache_get, cache_set

router = APIRouter(prefix="/schemes", tags=["Schemes"])
settings = get_settings()


@router.get("", response_model=SchemeListResponse)
async def list_schemes(
    state: str | None = None,
    category: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> SchemeListResponse:
    cache_key = f"schemes:{state}:{category}:{search}:{page}:{page_size}"
    cached = await cache_get(cache_key)
    if cached:
        return SchemeListResponse.model_validate(cached)

    stmt = select(Scheme).where(Scheme.is_active.is_(True))

    if state:
        stmt = stmt.where(
            or_(
                Scheme.applicable_states.contains(["All India"]),
                Scheme.applicable_states.contains([state.title()]),
            )
        )
    if category:
        stmt = stmt.where(func.lower(Scheme.category) == category.lower())
    if search:
        term = f"%{search.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Scheme.name).like(term),
                func.lower(Scheme.short_description).like(term),
            )
        )

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.order_by(Scheme.name).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    schemes = result.scalars().all()

    response = SchemeListResponse(
        schemes=[SchemeSummary.model_validate(s) for s in schemes],
        total=total,
        page=page,
        page_size=page_size,
    )
    await cache_set(cache_key, response.model_dump(), ttl_seconds=600)
    return response


@router.get("/categories/list")
async def list_categories(db: AsyncSession = Depends(get_db)) -> dict:
    cached = await cache_get("schemes:categories")
    if cached:
        return cached

    result = await db.execute(
        select(Scheme.category, func.count())
        .where(Scheme.is_active.is_(True))
        .group_by(Scheme.category)
        .order_by(Scheme.category)
    )
    categories = [{"name": row[0], "count": row[1]} for row in result.all()]
    payload = {"categories": categories, "total": len(categories)}
    await cache_set("schemes:categories", payload, ttl_seconds=3600)
    return payload


@router.get("/{scheme_id}", response_model=SchemeDetail)
async def get_scheme(
    scheme_id: str,
    db: AsyncSession = Depends(get_db),
) -> SchemeDetail:
    cache_key = f"scheme:{scheme_id}"
    cached = await cache_get(cache_key)
    if cached:
        return SchemeDetail.model_validate(cached)

    result = await db.execute(
        select(Scheme)
        .options(selectinload(Scheme.eligibility_rules))
        .where(Scheme.id == scheme_id)
    )
    scheme = result.scalar_one_or_none()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    detail = SchemeDetail.model_validate(scheme)
    await cache_set(cache_key, detail.model_dump(), ttl_seconds=3600)
    return detail
