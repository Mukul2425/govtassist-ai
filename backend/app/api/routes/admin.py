"""Admin API for scheme ingestion (protected by API key)."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.database import get_db
from app.models.scheme import EligibilityRule, GovernmentLevel, Scheme, SchemeDocument
from app.rag.embeddings import embed_all_documents
from app.services.cache_service import cache_delete_pattern

router = APIRouter(prefix="/admin", tags=["Admin"])
settings = get_settings()


class EligibilityRuleInput(BaseModel):
    field: str
    operator: str
    value: object
    is_required: bool = True
    description: str | None = None


class DocumentInput(BaseModel):
    title: str
    content: str
    source_url: str


class SchemeCreateRequest(BaseModel):
    id: str = Field(..., min_length=3, max_length=32, pattern=r"^SCH_[A-Z0-9_]+$")
    name: str = Field(..., min_length=5, max_length=512)
    short_description: str
    full_description: str
    government_level: GovernmentLevel
    ministry: str | None = None
    category: str
    applicable_states: list[str]
    benefits: list[str]
    required_documents: list[str]
    application_process: str
    application_url: str | None = None
    official_source_url: str
    keywords: list[str] = Field(default_factory=list)
    rules: list[EligibilityRuleInput] = Field(default_factory=list)
    documents: list[DocumentInput] = Field(default_factory=list)


def verify_admin_key(x_admin_key: str = Header(...)) -> None:
    if not settings.admin_api_key or x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid admin API key")


@router.post("/schemes", dependencies=[Depends(verify_admin_key)])
async def create_scheme(
    payload: SchemeCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    now = datetime.now(UTC)
    scheme = Scheme(
        id=payload.id,
        name=payload.name,
        short_description=payload.short_description,
        full_description=payload.full_description,
        government_level=payload.government_level,
        ministry=payload.ministry,
        category=payload.category,
        applicable_states=payload.applicable_states,
        benefits=payload.benefits,
        required_documents=payload.required_documents,
        application_process=payload.application_process,
        application_url=payload.application_url,
        official_source_url=payload.official_source_url,
        keywords=payload.keywords,
        verified_at=now,
        is_active=True,
    )
    db.add(scheme)
    await db.flush()

    for rule in payload.rules:
        db.add(EligibilityRule(scheme_id=scheme.id, **rule.model_dump()))

    for i, doc in enumerate(payload.documents):
        db.add(
            SchemeDocument(
                scheme_id=scheme.id,
                title=doc.title,
                content=doc.content,
                chunk_index=i,
                source_url=doc.source_url,
            )
        )

    await db.commit()
    embedded = await embed_all_documents(db)
    await cache_delete_pattern("schemes:*")
    await cache_delete_pattern("scheme:*")

    return {"status": "created", "scheme_id": scheme.id, "embeddings_generated": embedded}
