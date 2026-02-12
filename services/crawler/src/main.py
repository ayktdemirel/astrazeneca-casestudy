import sys
sys.path.append("/app")

from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime
import asyncio
import uuid
import json

from libs.shared.src.logger import setup_logger
from libs.shared.src.middleware import CorrelationIdMiddleware
from .database import get_db, engine, Base, AsyncSessionLocal
from . import models, schemas
from libs.shared.src.exceptions import setup_exception_handlers
from libs.shared.src.auth import get_current_user, require_role, ROLE_ADMIN, ROLE_ANALYST, ROLE_EXECUTIVE, User

logger = setup_logger("crawler-service")

app = FastAPI(
    title="Crawler Service",
    description="Manages crawl jobs and documents ingestion from external sources.",
    version="1.0.0"
)

app.add_middleware(CorrelationIdMiddleware)
setup_exception_handlers(app)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "crawler-service"}

@app.post("/api/crawl/jobs", response_model=schemas.CrawlJobResponse, status_code=status.HTTP_201_CREATED)
async def create_crawl_job(
    job: schemas.CrawlJobCreate, 
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role([ROLE_ADMIN]))
):
    db_job = models.CrawlJob(
        source=job.source,
        query=job.query,
        schedule=job.schedule,
        enabled=job.enabled
    )
    db.add(db_job)
    await db.commit()
    await db.refresh(db_job)
    logger.info(f"Created crawl job {db_job.id}")
    return db_job

@app.get("/api/crawl/jobs", response_model=list[schemas.CrawlJobResponse])
async def list_crawl_jobs(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role([ROLE_ADMIN]))
):
    result = await db.execute(select(models.CrawlJob))
    return result.scalars().all()

@app.delete("/api/crawl/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_crawl_job(job_id: str, db: AsyncSession = Depends(get_db)):
    job = await db.get(models.CrawlJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    # Delete associated runs first
    await db.execute(delete(models.CrawlRun).where(models.CrawlRun.job_id == job_id))
    await db.delete(job)
    await db.commit()
    logger.info(f"Deleted crawl job {job_id}")

@app.put("/api/crawl/jobs/{job_id}", response_model=schemas.CrawlJobResponse)
async def update_crawl_job(job_id: str, updates: schemas.CrawlJobUpdate, db: AsyncSession = Depends(get_db)):
    job = await db.get(models.CrawlJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(job, field, value)
    await db.commit()
    await db.refresh(job)
    logger.info(f"Updated crawl job {job_id}")
    return job

from .clients.scrapers import get_scrapers
from .clients.clinical_trials import ClinicalTrialsFetcher

# Mock crawl function -> upgraded to Real Scraper
async def run_crawl_task(run_id: str, job_id: str):
    logger.info(f"Starting crawl run {run_id} for job {job_id}")
    # Summarizer removed - now handled by Insight Classification Service
    ct_fetcher = ClinicalTrialsFetcher()
    
    async with AsyncSessionLocal() as session:
        try:
            job = await session.get(models.CrawlJob, job_id)
            source_filter = job.source if job else "All"
            query_filter = job.query if job else None
            docs_created = 0
            
            # 1. Health & Research News Scraping
            if source_filter in ["All", "ResearchNews"]:
                scrapers = get_scrapers()
                for scraper in scrapers:
                    articles = await scraper.scrape()
                    for article in articles:
                        # Filter by query keywords if provided
                        if query_filter:
                            keywords = [kw.strip().lower() for kw in query_filter.split(",")]
                            text = (article.get('title', '') + ' ' + article.get('content', '')).lower()
                            if not any(kw in text for kw in keywords):
                                continue
                        # Check if already ingested (by link)
                        exists = await session.execute(select(models.Document).where(models.Document.external_id == article['link']))
                        if exists.scalar_one_or_none(): continue
                        
                        # Save as Document (single source of truth)
                        doc_id = f"news-{uuid.uuid4().hex[:8]}"
                        doc = models.Document(
                            id=doc_id,
                            source=article['source'],
                            external_id=article['link'],
                            url=article['link'],
                            title=article['title'],
                            raw_content=json.dumps(article, default=str), 
                            published_date=datetime.now(),
                            processed=False 
                        )
                        session.add(doc)
                        docs_created += 1

            # 2. Clinical Trials Scraping
            if source_filter in ["All", "ClinicalTrials"]:
                studies = await ct_fetcher.fetch_recent_studies(query=query_filter, limit=10)
                for study in studies:
                     # Check exist
                    exists = await session.execute(select(models.Document).where(models.Document.external_id == study['nctId']))
                    if exists.scalar_one_or_none(): continue
                    
                    doc_id = f"ct-{uuid.uuid4().hex[:8]}"
                    doc = models.Document(
                        id=doc_id,
                        source="ClinicalTrials",
                        external_id=study['nctId'],
                        url=study['url'],
                        title=study['title'],
                        raw_content=json.dumps(study),
                        published_date=datetime.now(),
                        processed=False 
                    )
                    session.add(doc)
                    docs_created += 1
            
            # Update run status
            run = await session.get(models.CrawlRun, run_id)
            if run:
                run.status = "COMPLETED"
                run.finished_at = datetime.utcnow()
                run.stats_json = {"documents_found": docs_created}
            
            await session.commit()
            logger.info(f"Completed crawl run {run_id}. Created {docs_created} docs")
        except Exception as e:
            logger.error(f"Crawl failed: {e}")
            await session.rollback()

@app.post("/api/crawl/run", response_model=schemas.CrawlRunResponse)
async def trigger_crawl_run(job_id: str, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    # Verify job exists
    result = await db.execute(select(models.CrawlJob).where(models.CrawlJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
         raise HTTPException(status_code=404, detail="Job not found")

    new_run = models.CrawlRun(
        job_id=job_id,
        status="STARTED"
    )
    db.add(new_run)
    await db.commit()
    await db.refresh(new_run)
    
    background_tasks.add_task(run_crawl_task, new_run.id, job_id)
    
    return new_run

@app.get("/api/crawl/documents", response_model=list[schemas.DocumentResponse])
async def list_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Document).order_by(models.Document.ingested_at.desc()))
    return result.scalars().all()
