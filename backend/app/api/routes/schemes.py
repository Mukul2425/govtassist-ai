from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import get_db
from app.models.scheme import Scheme
from app.schemas.scheme import SchemeDetail, SchemeListResponse, SchemeSummary

router = APIRouter(prefix="/schemes", tags=["Schemes"])


@router.get("", response_model=SchemeListResponse)
async def list_schemes(
    state: str | None = None,
    category: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> SchemeListResponse:
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

    return SchemeListResponse(
        schemes=[SchemeSummary.model_validate(s) for s in schemes],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{scheme_id}", response_model=SchemeDetail)
async def get_scheme(
    scheme_id: str,
    db: AsyncSession = Depends(get_db),
) -> SchemeDetail:
    result = await db.execute(
        select(Scheme)
        .options(selectinload(Scheme.eligibility_rules))
        .where(Scheme.id == scheme_id)
    )
    scheme = result.scalar_one_or_none()
    if not scheme:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Scheme not found")

    return SchemeDetail.model_validate(scheme)
