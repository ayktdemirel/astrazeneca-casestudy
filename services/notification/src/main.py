import sys
sys.path.append("/app")

from fastapi import FastAPI, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, select
from typing import List, Optional
import uuid
import logging
from datetime import datetime

from libs.shared.src.logger import setup_logger, correlation_id_ctx
from libs.shared.src.middleware import CorrelationIdMiddleware
from .database import get_db, engine, Base
from . import models, schemas
from libs.shared.src.exceptions import setup_exception_handlers
from libs.shared.src.auth import get_current_user, require_role, ROLE_ADMIN, ROLE_ANALYST, ROLE_EXECUTIVE, User

logger = setup_logger("notification-service")

app = FastAPI(title="Notification Service")

app.add_middleware(CorrelationIdMiddleware)
setup_exception_handlers(app)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "notification-service"}

@app.post("/api/subscriptions", response_model=schemas.SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    sub: schemas.SubscriptionCreate, 
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not sub.therapeuticAreas and not sub.competitorIds:
        raise HTTPException(status_code=400, detail="At least one preference (therapeuticAreas or competitorIds) is required")

    new_id = f"sub-{uuid.uuid4().hex[:8]}"
    db_sub = models.Subscription(
        id=new_id,
        user_id=user.user_id,
        therapeutic_areas=sub.therapeuticAreas,
        competitor_ids=sub.competitorIds,
        channels=sub.channels
    )
    db.add(db_sub)
    await db.commit()
    await db.refresh(db_sub)
    logger.info(f"Created subscription {new_id} for user {user.user_id}")
    return db_sub

@app.get("/api/subscriptions", response_model=List[schemas.SubscriptionResponse])
async def list_subscriptions(db: AsyncSession = Depends(get_db)):
    # Admin view - list all
    result = await db.execute(select(models.Subscription))
    return result.scalars().all()

@app.post("/api/notifications/send", status_code=status.HTTP_200_OK)
async def send_notification(
    req: schemas.NotificationSendRequest, 
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role([ROLE_ADMIN]))
):
    # 1. Verify subscription
    sub_query = await db.execute(select(models.Subscription).where(models.Subscription.id == req.subscriptionId))
    sub = sub_query.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    # 2. In a real system, we'd fetch the insight details here to include in the payload
    # For now, we mock the payload
    payload = {
        "insight_id": req.insightId,
        "message": "New insight matches your subscription preferences."
    }

    # 3. "Send" the notification (Mock)
    logger.info(f"SENDING NOTIFICATION via {sub.channels} to user {sub.user_id}: {payload}")

    # 4. Record history
    notif_id = f"notif-{uuid.uuid4().hex[:8]}"
    correlation_id = correlation_id_ctx.get()
    
    history_entry = models.NotificationHistory(
        id=notif_id,
        user_id=sub.user_id,
        subscription_id=sub.id,
        insight_id=req.insightId,
        status="SENT",
        payload_json=payload,
        correlation_id=correlation_id,
        read=False,
        sent_at=datetime.utcnow()
    )
    db.add(history_entry)
    await db.commit()
    
    return {"notificationId": notif_id, "status": "SENT"}

@app.get("/api/notifications", response_model=List[schemas.NotificationHistoryResponse])
async def list_notifications_history(db: AsyncSession = Depends(get_db)):
    # Admin view
    result = await db.execute(select(models.NotificationHistory).order_by(desc(models.NotificationHistory.sent_at)))
    return result.scalars().all()

@app.get("/api/notifications/me", response_model=List[schemas.NotificationHistoryResponse])
async def get_my_notifications(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(models.NotificationHistory)
        .where(models.NotificationHistory.user_id == user.user_id)
        .order_by(desc(models.NotificationHistory.sent_at))
    )
    return result.scalars().all()

@app.post("/api/notifications/trigger", status_code=status.HTTP_200_OK)
async def trigger_notification(req: schemas.TriggerNotificationRequest, db: AsyncSession = Depends(get_db)):
    conditions = []
    
    if req.therapeutic_area:
        # Check if therapeutic_area is in the subscription's therapeutic_areas array
        conditions.append(models.Subscription.therapeutic_areas.any(req.therapeutic_area))
        
    if req.competitor_id:
        # Check if competitor_id is in the subscription's competitor_ids array
        conditions.append(models.Subscription.competitor_ids.any(req.competitor_id))
    
    if not conditions:
        return {"status": "skipped", "reason": "No matching criteria in insight"}

    # Find subscriptions matching ANY condition
    from sqlalchemy import or_
    query = select(models.Subscription).where(or_(*conditions))
    result = await db.execute(query)
    subscriptions = result.scalars().all()
    
    sent_count = 0
    for sub in subscriptions:
        # Dedup: skip if user already received notification for this insight
        existing = await db.execute(
            select(models.NotificationHistory).where(
                models.NotificationHistory.insight_id == req.insight_id,
                models.NotificationHistory.user_id == sub.user_id
            )
        )
        if existing.scalar_one_or_none():
            logger.info(f"Skipping duplicate notification for user {sub.user_id}, insight {req.insight_id}")
            continue
        
        # Create Payload
        payload = {
            "insight_id": req.insight_id,
            "title": req.title,
            "description": req.description,
            "therapeutic_area": req.therapeutic_area,
            "message": f"New Insight: {req.title}"
        }
        
        logger.info(f"TRIGGER: Sending notification to user {sub.user_id} via {sub.channels}")
        
        # Record History
        notif_id = f"notif-{uuid.uuid4().hex[:8]}"
        correlation_id = correlation_id_ctx.get()
        
        history_entry = models.NotificationHistory(
            id=notif_id,
            user_id=sub.user_id,
            subscription_id=sub.id,
            insight_id=req.insight_id,
            status="SENT",
            payload_json=payload,
            correlation_id=correlation_id,
            read=False,
            sent_at=datetime.utcnow()
        )
        db.add(history_entry)
        sent_count += 1
        
    await db.commit()
    return {"status": "ok", "matched_subscriptions": len(subscriptions), "sent_notifications": sent_count}
