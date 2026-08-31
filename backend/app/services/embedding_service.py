"""Unified embedding generation with OpenAI primary and deterministic local fallback."""

import hashlib
import math
import re

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()
EMBEDDING_DIM = 1536


def local_embed(text: str, dim: int = EMBEDDING_DIM) -> list[float]:
    """Deterministic hash-based embedding for dev/mock mode (no API key required)."""
    vec = [0.0] * dim
    tokens = re.findall(r"\w+", text.lower())
    for token in tokens:
        digest = hashlib.sha256(token.encode()).digest()
        for i, byte in enumerate(digest):
            idx = (byte + i * 31) % dim
            vec[idx] += float(byte) / 255.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


class EmbeddingService:
    def __init__(self) -> None:
        self._client: AsyncOpenAI | None = None
        if settings.openai_api_key and not settings.llm_mock_mode:
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    @property
    def using_openai(self) -> bool:
        return self._client is not None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    async def embed(self, text: str) -> list[float]:
        if self._client:
            response = await self._client.embeddings.create(
                model=settings.openai_embedding_model,
                input=text[:8000],
            )
            return response.data[0].embedding
        return local_embed(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self._client:
            response = await self._client.embeddings.create(
                model=settings.openai_embedding_model,
                input=[t[:8000] for t in texts],
            )
            return [item.embedding for item in response.data]
        return [local_embed(t) for t in texts]


embedding_service = EmbeddingService()
