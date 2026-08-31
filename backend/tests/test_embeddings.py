"""Tests for embedding service."""

from app.services.embedding_service import EMBEDDING_DIM, local_embed


def test_local_embed_dimension():
    vec = local_embed("farmer from punjab with 2 acres land")
    assert len(vec) == EMBEDDING_DIM


def test_local_embed_deterministic():
    a = local_embed("test query")
    b = local_embed("test query")
    assert a == b


def test_local_embed_different_text():
    a = local_embed("farmer")
    b = local_embed("student graduate")
    assert a != b
