import sys
sys.path.append("/app")

from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import uuid
import logging

from libs.shared.src.logger import setup_logger
from libs.shared.src.middleware import CorrelationIdMiddleware
from .database import get_db, engine, Base
from . import models, schemas
from libs.shared.src.exceptions import setup_exception_handlers
from libs.shared.src.auth import get_current_user, require_role, ROLE_ADMIN, ROLE_ANALYST, ROLE_EXECUTIVE, User

logger = setup_logger("insights-service")

app = FastAPI(title="Insights Service")

app.add_middleware(CorrelationIdMiddleware)
setup_exception_handlers(app)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "insights-service"}

def calculate_relevance(impact_level: Optional[str], current_score: Optional[float]) -> Optional[float]:
    if current_score is not None:
        return current_score
    
    if not impact_level:
        return None
    
    level = impact_level.lower()
    if level == "high":
        return 9.0
    elif level == "medium":
        return 6.0
    elif level == "low":
        return 3.0
    return 0.0 # Default if impact is provided but not recognized

@app.post("/api/insights", response_model=schemas.InsightResponse, status_code=status.HTTP_201_CREATED)
async def create_insight(
    insight: schemas.InsightCreate, 
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role([ROLE_ADMIN, ROLE_ANALYST]))
):
    # Calculate relevance score
    relevance_score = calculate_relevance(insight.impact_level, insight.relevance_score)
    
    new_id = f"insight-{uuid.uuid4().hex[:8]}"
    db_insight = models.Insight(
        id=new_id,
        title=insight.title,
        description=insight.description,
        category=insight.category,
        therapeutic_area=insight.therapeutic_area,
        competitor_id=insight.competitor_id,
        impact_level=insight.impact_level,
        relevance_score=relevance_score,
        source=insight.source,
        published_date=insight.published_date,
        source_document_id=insight.source_document_id
    )
    db.add(db_insight)
    await db.commit()
    await db.refresh(db_insight)
    logger.info(f"Created insight {new_id} with relevance {relevance_score}")
    
    # In a real event-driven system, we would emit 'insight.created' here.
    return db_insight

@app.get("/api/insights", response_model=List[schemas.InsightResponse])
async def list_insights(
    therapeuticArea: Optional[str] = Query(None),
    competitorId: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    query = select(models.Insight).order_by(models.Insight.created_at.desc())
    if therapeuticArea:
        query = query.where(models.Insight.therapeutic_area == therapeuticArea)
    if competitorId:
        query = query.where(models.Insight.competitor_id == competitorId)
        
    logger.info(f"Executing query: {query}")
    result = await db.execute(query)
    insights = result.scalars().all()
    logger.info(f"Found {len(insights)} insights")
    return insights

@app.get("/api/insights/{id}", response_model=schemas.InsightResponse)
async def get_insight(
    id: str, 
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    result = await db.execute(select(models.Insight).where(models.Insight.id == id))
    insight = result.scalar_one_or_none()
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    return insight

@app.delete("/api/insights/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_insight(
    id: str, 
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role([ROLE_ADMIN]))
):
    result = await db.execute(select(models.Insight).where(models.Insight.id == id))
    insight = result.scalar_one_or_none()
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    
    await db.delete(insight)
    await db.commit()
    logger.info(f"Deleted insight {id}")
    return None

@app.put("/api/insights/{id}", response_model=schemas.InsightResponse)
async def update_insight(
    id: str, 
    updates: schemas.InsightUpdate, 
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role([ROLE_ADMIN, ROLE_ANALYST]))
):
    result = await db.execute(select(models.Insight).where(models.Insight.id == id))
    insight = result.scalar_one_or_none()
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    
    update_data = updates.model_dump(exclude_unset=True, by_alias=False)
    for field, value in update_data.items():
        setattr(insight, field, value)
    
    # Recalculate relevance if impact_level changed but score wasn't explicitly set
    if 'impact_level' in update_data and 'relevance_score' not in update_data:
        insight.relevance_score = calculate_relevance(insight.impact_level, None)
    
    await db.commit()
    await db.refresh(insight)
    logger.info(f"Updated insight {id}")
    return insight
