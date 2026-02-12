import pytest
from httpx import AsyncClient
from src.main import app
import uuid
from jose import jwt
import os

# Mock Secret
SECRET = os.getenv("JWT_SECRET", "super-secret-key-change-me")

def create_test_token(role: str = "ADMIN"):
    payload = {
        "sub": "test@example.com",
        "role": role,
        "userId": "test-user-id"
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")

@pytest.mark.asyncio
async def test_create_insight():
    unique_title = f"Insight {uuid.uuid4()}"
    token = create_test_token("ANALYST")
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/insights", json={
            "title": unique_title,
            "description": "Details about competitor activity...",
            "therapeuticArea": "Oncology",
            "competitorId": "comp-123", # No strict FK check in model
            "impactLevel": "High",
            "publishedDate": "2024-01-01"
        }, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == unique_title
    assert "id" in data
    assert data["relevanceScore"] == 9.0

@pytest.mark.asyncio
async def test_list_insights_filter():
    unique_area = f"Area-{uuid.uuid4()}"
    token = create_test_token("ANALYST")
    async with AsyncClient(app=app, base_url="http://test") as ac:
        await ac.post("/api/insights", json={
            "title": "Unique Area Insight",
            "therapeuticArea": unique_area,
            "impactLevel": "High"
        }, headers={"Authorization": f"Bearer {token}"})
        
        # List with filter
        response = await ac.get(f"/api/insights?therapeuticArea={unique_area}", headers={"Authorization": f"Bearer {token}"})
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    # Ensure at least one matches our unique area
    assert any(i["therapeuticArea"] == unique_area for i in data)

@pytest.mark.asyncio
async def test_get_insight_by_id():
    unique_title = f"Get Insight {uuid.uuid4()}"
    token = create_test_token("ANALYST")
    async with AsyncClient(app=app, base_url="http://test") as ac:
        create_res = await ac.post("/api/insights", json={
            "title": unique_title,
            "therapeuticArea": "Rare Disease",
            "impactLevel": "Low"
        }, headers={"Authorization": f"Bearer {token}"})
        insight_id = create_res.json()["id"]

        read_res = await ac.get(f"/api/insights/{insight_id}", headers={"Authorization": f"Bearer {token}"})
    
    assert read_res.status_code == 200
    assert read_res.json()["id"] == insight_id
    assert read_res.json()["relevanceScore"] == 3.0
