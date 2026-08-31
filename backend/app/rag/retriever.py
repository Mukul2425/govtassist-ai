"""RAG retrieval using pgvector semantic search with text fallback."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.logging_config import get_logger
from app.models.scheme import SchemeDocument
from app.services.embedding_service import embedding_service

logger = get_logger(__name__)


async def retrieve_scheme_context(
    session: AsyncSession,
    scheme_id: str,
    query: str,
    top_k: int = 3,
) -> list[str]:
    """Retrieve relevant document chunks for a scheme via vector similarity."""
    try:
        query_vector = await embedding_service.embed(f"{query} {scheme_id}")
        result = await session.execute(
            select(SchemeDocument)
            .where(SchemeDocument.scheme_id == scheme_id)
            .where(SchemeDocument.embedding.isnot(None))
            .order_by(SchemeDocument.embedding.cosine_distance(query_vector))
            .limit(top_k)
        )
        docs = result.scalars().all()
        if docs:
            return [f"{doc.title}: {doc.content[:500]}" for doc in docs]
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
