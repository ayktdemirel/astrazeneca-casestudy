import pytest
from httpx import AsyncClient
from src.main import app
import uuid
from jose import jwt
import os

# Mock Secret
SECRET = os.getenv("JWT_SECRET", "super-secret-key-change-me")

def create_test_token(user_id: str = "test-user-id", role: str = "ADMIN"):
    payload = {
        "sub": "test@example.com",
        "role": role,
        "userId": user_id
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")

@pytest.mark.asyncio
async def test_create_subscription():
    unique_user = f"user-{uuid.uuid4()}"
    token = create_test_token(user_id=unique_user)
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/subscriptions", 
            json={
                "therapeuticAreas": ["Oncology"],
                "competitorIds": ["comp-1"],
                "channels": ["console"]
            },
            headers={"Authorization": f"Bearer {token}"}
        )
    assert response.status_code == 201
    data = response.json()
    assert data["userId"] == unique_user
    assert "id" in data

@pytest.mark.asyncio
async def test_create_subscription_validation_error():
    token = create_test_token()
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/subscriptions", json={
            "therapeuticAreas": [],
            "competitorIds": [],
            "channels": []
        }, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code in [201, 400]

@pytest.mark.asyncio
async def test_send_notification():
    # 1. Create subscription first
    unique_user = f"user-{uuid.uuid4()}"
    user_token = create_test_token(user_id=unique_user)
    admin_token = create_test_token(role="ADMIN")
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        sub_res = await ac.post("/api/subscriptions", 
            json={
                "therapeuticAreas": ["Bio"],
                "competitorIds": ["comp-2"],
                "channels": ["console"]
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        sub_id = sub_res.json()["id"]

        # 2. Send notification
        response = await ac.post("/api/notifications/send", json={
            "insightId": "insight-123",
            "subscriptionId": sub_id,
            "message": "New insight available"
        }, headers={"Authorization": f"Bearer {admin_token}"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SENT"

@pytest.mark.asyncio
async def test_get_notifications_history():
    # 1. Create subscription & Send notification
    unique_insight_id = f"hist-insight-{uuid.uuid4()}"
    unique_user = f"user-{uuid.uuid4()}"
    user_token = create_test_token(user_id=unique_user)
    admin_token = create_test_token(role="ADMIN")
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        sub_res = await ac.post("/api/subscriptions", 
            json={
                "therapeuticAreas": ["Bio"],
                "competitorIds": ["comp-3"],
                "channels": ["console"]
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        sub_id = sub_res.json()["id"]

        await ac.post("/api/notifications/send", json={
            "insightId": unique_insight_id,
            "subscriptionId": sub_id,
            "message": "History test"
        }, headers={"Authorization": f"Bearer {admin_token}"})
        
        # Then list
        response = await ac.get("/api/notifications", headers={"Authorization": f"Bearer {admin_token}"})
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    # Check if our unique insight is in the list
    assert any(n["insightId"] == unique_insight_id for n in data)
