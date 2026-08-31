"""Pytest configuration and fixtures."""

import os

os.environ.setdefault("LLM_MOCK_MODE", "true")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://govtassist:govtassist@localhost:5432/govtassist_test",
)
