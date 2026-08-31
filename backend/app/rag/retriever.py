"""RAG retrieval using pgvector semantic search."""

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.logging_config import get_logger
from app.models.scheme import SchemeDocument
from app.services.llm_service import llm_service

logger = get_logger(__name__)


async def retrieve_scheme_context(
    session: AsyncSession,
    scheme_id: str,
    query: str,
    top_k: int = 3,
) -> list[str]:
    """Retrieve relevant document chunks for a scheme."""
    if llm_service.is_available:
        try:
            embedding = await llm_service.embed(f"{query} {scheme_id}")
            result = await session.execute(
                text("""
                    SELECT content, title
                    FROM scheme_documents
                    WHERE scheme_id = :scheme_id
                      AND embedding IS NOT NULL
                    ORDER BY embedding <=> :embedding
                    LIMIT :top_k
                """),
                {"scheme_id": scheme_id, "embedding": str(embedding), "top_k": top_k},
            )
            rows = result.fetchall()
            if rows:
                return [f"{row.title}: {row.content[:500]}" for row in rows]
        except Exception as e:
            logger.warning("vector_search_failed", error=str(e), scheme_id=scheme_id)

    result = await session.execute(
        select(SchemeDocument)
        .where(SchemeDocument.scheme_id == scheme_id)
        .order_by(SchemeDocument.chunk_index)
        .limit(top_k)
    )
    docs = result.scalars().all()
    return [f"{doc.title}: {doc.content[:500]}" for doc in docs]
