"""Generate and persist document embeddings for RAG."""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.logging_config import get_logger
from app.models.scheme import SchemeDocument
from app.services.embedding_service import embedding_service

logger = get_logger(__name__)


async def embed_all_documents(session: AsyncSession, batch_size: int = 20) -> int:
    """Generate embeddings for documents missing them. Returns count updated."""
    result = await session.execute(
        select(SchemeDocument).where(SchemeDocument.embedding.is_(None))
    )
    docs = list(result.scalars().all())
    if not docs:
        logger.info("embeddings_up_to_date")
        return 0

    updated = 0
    for i in range(0, len(docs), batch_size):
        batch = docs[i : i + batch_size]
        texts = [f"{d.title}\n{d.content}" for d in batch]
        vectors = await embedding_service.embed_batch(texts)
        for doc, vector in zip(batch, vectors, strict=True):
            await session.execute(
                update(SchemeDocument)
                .where(SchemeDocument.id == doc.id)
                .values(embedding=vector)
            )
            updated += 1

    await session.commit()
    logger.info(
        "embeddings_generated",
        count=updated,
        provider="openai" if embedding_service.using_openai else "local",
    )
    return updated
