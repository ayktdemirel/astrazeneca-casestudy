import pytest
from httpx import AsyncClient
from src.main import app
from src.database import get_db, Base, engine
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
async def test_create_competitor():
    unique_name = f"Test Pharma {uuid.uuid4()}"
    token = create_test_token("ANALYST")
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/competitors", json={
            "name": unique_name,
            "therapeuticAreas": ["Oncology"],
            "headquarters": "Test City",
            "activeDrugs": 5,
            "pipelineDrugs": 10
        }, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == unique_name
    assert "id" in data

@pytest.mark.asyncio
async def test_get_competitor_by_id():
    unique_name = f"Read Pharma {uuid.uuid4()}"
    token = create_test_token("ANALYST")
    async with AsyncClient(app=app, base_url="http://test") as ac:
        create_res = await ac.post("/api/competitors", json={
            "name": unique_name,
            "therapeuticAreas": ["Cardio"],
            "headquarters": "Read City"
        }, headers={"Authorization": f"Bearer {token}"})
        competitor_id = create_res.json()["id"]

        # Then read it back
        response = await ac.get(f"/api/competitors/{competitor_id}", headers={"Authorization": f"Bearer {token}"})
    
    assert response.status_code == 200
    assert response.json()["name"] == unique_name

@pytest.mark.asyncio
async def test_add_clinical_trial():
    unique_name = f"Trial Pharma {uuid.uuid4()}"
    token = create_test_token("ADMIN")
    async with AsyncClient(app=app, base_url="http://test") as ac:
        comp = await ac.post("/api/competitors", json={"name": unique_name}, headers={"Authorization": f"Bearer {token}"})
        comp_id = comp.json()["id"]

        # Add trial
        trial_id = f"NCT{uuid.uuid4().hex[:8]}"
        trial_data = {
            "trialId": trial_id,
            "drugName": "TestDrug",
            "phase": "Phase 1",
            "indication": "Headache",
            "status": "Recruiting",
            "startDate": "2024-01-01",
            "estimatedCompletion": "2025-01-01",
            "enrollmentTarget": 100
        }
        response = await ac.post(f"/api/competitors/{comp_id}/trials", json=trial_data, headers={"Authorization": f"Bearer {token}"})
    
    assert response.status_code == 201
    assert response.json()["trialId"] == trial_id
    assert response.json()["competitorId"] == comp_id

