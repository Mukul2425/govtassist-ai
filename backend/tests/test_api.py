"""API integration tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "llm_available" in data


@pytest.mark.asyncio
async def test_list_schemes(client: AsyncClient):
    response = await client.get("/api/v1/schemes?page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert "schemes" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_recommendations_haryana_graduate(client: AsyncClient):
    response = await client.post(
        "/api/v1/recommendations",
        json={
            "query": "I am 23 years old, a graduate from Haryana, family income is 4 lakh",
            "max_results": 5,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"]
    assert data["extracted_profile"]["state"] == "Haryana"
    assert data["extracted_profile"]["annual_family_income"] == 400000
    assert len(data["recommendations"]) > 0


@pytest.mark.asyncio
async def test_recommendations_session_continuation(client: AsyncClient):
    first = await client.post(
        "/api/v1/recommendations",
        json={"query": "I am a graduate from Haryana", "max_results": 5},
    )
    assert first.status_code == 200
    session_id = first.json()["session_id"]

    second = await client.post(
        "/api/v1/recommendations",
        json={
            "query": "My family income is 4 lakh and I am 23 years old",
            "session_id": session_id,
            "max_results": 5,
        },
    )
    assert second.status_code == 200
    profile = second.json()["extracted_profile"]
    assert profile.get("state") == "Haryana"
    assert profile.get("annual_family_income") == 400000
    assert profile.get("age") == 23


@pytest.mark.asyncio
async def test_admin_requires_key(client: AsyncClient):
    response = await client.post(
        "/api/v1/admin/schemes",
        json={
            "id": "SCH_TEST_X",
            "name": "Test Scheme",
            "short_description": "Test",
            "full_description": "Test full",
            "government_level": "central",
            "category": "Test",
            "applicable_states": ["All India"],
            "benefits": ["Test benefit"],
            "required_documents": ["Aadhaar"],
            "application_process": "Apply online",
            "official_source_url": "https://example.com",
        },
        headers={"X-Admin-Key": "wrong-key"},
    )
    assert response.status_code == 403
