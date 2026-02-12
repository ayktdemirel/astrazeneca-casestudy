import sys
sys.path.append("/app")

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List
import uuid
import logging

from libs.shared.src.logger import setup_logger
from libs.shared.src.middleware import CorrelationIdMiddleware
from .database import get_db, engine, Base
from . import models, schemas
from libs.shared.src.exceptions import setup_exception_handlers
from libs.shared.src.auth import get_current_user, require_role, ROLE_ADMIN, ROLE_ANALYST, ROLE_EXECUTIVE, User

logger = setup_logger("competitor-service")

app = FastAPI(title="Competitor Service")

app.add_middleware(CorrelationIdMiddleware)
setup_exception_handlers(app)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "competitor-service"}

@app.post("/api/competitors", response_model=schemas.CompetitorResponse, status_code=status.HTTP_201_CREATED)
async def create_competitor(
    competitor: schemas.CompetitorCreate, 
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role([ROLE_ADMIN, ROLE_ANALYST]))
):
    new_id = f"comp-{uuid.uuid4().hex[:8]}"
    db_competitor = models.Competitor(
        id=new_id,
        name=competitor.name,
        headquarters=competitor.headquarters,
        therapeutic_areas=competitor.therapeuticAreas,
        active_drugs=competitor.activeDrugs,
        pipeline_drugs=competitor.pipelineDrugs
    )
    db.add(db_competitor)
    await db.commit()
    await db.refresh(db_competitor)
    logger.info(f"Created competitor {new_id}")
    return db_competitor

@app.get("/api/competitors", response_model=List[schemas.CompetitorResponse])
async def list_competitors(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role([ROLE_ADMIN, ROLE_ANALYST, ROLE_EXECUTIVE]))
):
    result = await db.execute(select(models.Competitor))
    competitors = result.scalars().all()
    return competitors

@app.get("/api/competitors/{id}", response_model=schemas.CompetitorResponse)
async def get_competitor(
    id: str, 
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role([ROLE_ADMIN, ROLE_ANALYST, ROLE_EXECUTIVE]))
):
    result = await db.execute(select(models.Competitor).where(models.Competitor.id == id))
    competitor = result.scalar_one_or_none()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return competitor

@app.put("/api/competitors/{id}", response_model=schemas.CompetitorResponse)
async def update_competitor(
    id: str, 
    competitor_update: schemas.CompetitorCreate, 
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role([ROLE_ADMIN, ROLE_ANALYST]))
):
    result = await db.execute(select(models.Competitor).where(models.Competitor.id == id))
    db_competitor = result.scalar_one_or_none()
    if not db_competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    
    db_competitor.name = competitor_update.name
    db_competitor.headquarters = competitor_update.headquarters
    db_competitor.therapeutic_areas = competitor_update.therapeuticAreas
    db_competitor.active_drugs = competitor_update.activeDrugs
    db_competitor.pipeline_drugs = competitor_update.pipelineDrugs
    
    await db.commit()
    await db.refresh(db_competitor)
    logger.info(f"Updated competitor {id}")
    return db_competitor

@app.delete("/api/competitors/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_competitor(
    id: str, 
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role([ROLE_ADMIN]))
):
    # Check if competitor exists
    result = await db.execute(select(models.Competitor).where(models.Competitor.id == id))
    db_competitor = result.scalar_one_or_none()
    
    if not db_competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    
    # Delete linked clinical trials first
    await db.execute(delete(models.ClinicalTrial).where(models.ClinicalTrial.competitor_id == id))
    
    # Delete the competitor
    await db.delete(db_competitor)
    await db.commit()
    logger.info(f"Deleted competitor {id} and associated trials")
    return None

@app.get("/api/competitors/{id}/trials", response_model=List[schemas.ClinicalTrialResponse])
async def list_trials(
    id: str, 
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role([ROLE_ADMIN, ROLE_ANALYST, ROLE_EXECUTIVE]))
):
    result = await db.execute(select(models.Competitor).where(models.Competitor.id == id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Competitor not found")
    trials = await db.execute(select(models.ClinicalTrial).where(models.ClinicalTrial.competitor_id == id))
    return trials.scalars().all()

@app.post("/api/competitors/{id}/trials", response_model=schemas.ClinicalTrialResponse, status_code=status.HTTP_201_CREATED)
async def add_clinical_trial(
    id: str, 
    trial: schemas.ClinicalTrialCreate, 
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role([ROLE_ADMIN, ROLE_ANALYST]))
):
    # Check if competitor exists
    result = await db.execute(select(models.Competitor).where(models.Competitor.id == id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Competitor not found")

    # Check for existing trial with same trial_id for this competitor
    existing_trial_result = await db.execute(
        select(models.ClinicalTrial).where(
            models.ClinicalTrial.competitor_id == id,
            models.ClinicalTrial.trial_id == trial.trialId
        )
    )
    existing_trial = existing_trial_result.scalar_one_or_none()

    if existing_trial:
        # Update existing
        existing_trial.drug_name = trial.drugName
        existing_trial.phase = trial.phase
        existing_trial.indication = trial.indication
        existing_trial.status = trial.status
        existing_trial.start_date = trial.startDate
        existing_trial.estimated_completion = trial.estimatedCompletion
        existing_trial.enrollment_target = trial.enrollmentTarget
        
        await db.commit()
        await db.refresh(existing_trial)
        logger.info(f"Updated existing trial {trial.trialId} for competitor {id}")
        return existing_trial
    else:
        # Create new
        new_trial_id = f"trial-{uuid.uuid4().hex[:8]}"
        db_trial = models.ClinicalTrial(
            id=new_trial_id,
            competitor_id=id,
            trial_id=trial.trialId,
            drug_name=trial.drugName,
            phase=trial.phase,
            indication=trial.indication,
            status=trial.status,
            start_date=trial.startDate,
            estimated_completion=trial.estimatedCompletion,
            enrollment_target=trial.enrollmentTarget
        )
        db.add(db_trial)
        await db.commit()
        await db.refresh(db_trial)
        logger.info(f"Added trial {new_trial_id} to competitor {id}")
        return db_trial
