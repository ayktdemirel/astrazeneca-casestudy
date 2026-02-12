import sys
sys.path.append("/app")

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import httpx
import logging
import os
import re
from datetime import datetime, timedelta
from jose import jwt

from libs.shared.src.logger import setup_logger
from libs.shared.src.middleware import CorrelationIdMiddleware
from . import models
from .database import engine, get_db, AsyncSessionLocal
from libs.shared.src.exceptions import setup_exception_handlers

logger = setup_logger("orchestrator")

app = FastAPI(
    title="Orchestrator Service",
    description="Central intelligence hub: LLM analysis, competitor matching, insight generation.",
    version="2.0.0"
)

app.add_middleware(CorrelationIdMiddleware)
setup_exception_handlers(app)

# Configuration
INSIGHTS_SERVICE_URL = os.getenv("INSIGHTS_SERVICE_URL", "http://insights-service:8000")
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8000")
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key-change-me")
ALGORITHM = "HS256"

from .clients.llm_client import LLMClient
from .clients.competitor_client import CompetitorClient

# Initialize Clients
llm_client = LLMClient()
comp_client = CompetitorClient()

def create_system_token():
    expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode = {
        "sub": "system-orchestrator",
        "role": "ADMIN",
        "userId": "system",
        "exp": expire
    }
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt

@app.on_event("startup")
async def startup_event():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(process_new_documents, 'interval', seconds=10)
    scheduler.start()
    logger.info("Background scheduler started")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "orchestrator"}

async def process_new_documents():
    logger.info("Polling for unprocessed documents...")
    async with AsyncSessionLocal() as session:
        # Find unprocessed documents
        result = await session.execute(select(models.Document).where(models.Document.processed == False).limit(5))
        documents = result.scalars().all()
        
        if not documents:
            return

        # Generate System Token
        token = create_system_token()
        headers = {"Authorization": f"Bearer {token}"}

        # Fetch Competitors list (used by LLM for intelligent matching)
        # Pass headers to client (assuming client updated to accept them)
        competitors = await comp_client.get_competitors(headers=headers)
        logger.info(f"Loaded {len(competitors)} competitors for AI matching")
        
        for doc in documents:
            try:
                logger.info(f"Processing document {doc.id}")
                
                # 1. Send document + competitor list to LLM for analysis
                full_text = f"{doc.title}\n{doc.raw_content or ''}"
                analysis = await llm_client.analyze_content(full_text, competitors=competitors)
                
                # Extract fields
                summary = analysis.get("summary", "No summary available.")
                therapeutic_area = analysis.get("therapeutic_area", "General")
                category = analysis.get("category", "General")
                impact_level = analysis.get("impact_level", "Low")
                relevance_score = analysis.get("relevance_score", 3.0)
                tags = analysis.get("tags", [])
                
                # Extract Entities
                entities = analysis.get("entities", {})
                company = entities.get("company", "N/A")
                drug = entities.get("drug", "N/A")
                phase = entities.get("phase", "N/A")
                indication = entities.get("indication", "N/A")
                
                # AI-matched competitor ID (returned directly by OpenAI)
                matched_comp_id = analysis.get("matched_competitor_id", None)
                
                description = f"{summary}\n\nEntities: {company}, {drug}, {phase}."

                # 2. INTELLIGENCE LOOP: If AI matched a competitor, link trial
                if matched_comp_id:
                    logger.info(f"AI matched document to competitor {matched_comp_id} (company: {company})")
                    
                    # Create Trial if this is a clinical trial or has drug+phase data
                    if category == "Clinical Trial" or (drug != 'N/A' and phase != 'N/A'):
                        logger.info(f"Creating trial for competitor {matched_comp_id}")
                        
                        # Try to extract a real NCT ID from the text
                        nct_match = re.search(r'NCT\d{8}', full_text)
                        trial_id = nct_match.group(0) if nct_match else f"EXT-{doc.id[:8]}"
                        
                        trial_payload = {
                            "trialId": trial_id,
                            "drugName": drug if drug != 'N/A' else "Unknown Candidate",
                            "phase": phase if phase != 'N/A' else "Unknown",
                            "indication": indication if indication != 'N/A' else doc.title,
                            "status": "New Intelligence",
                            "startDate": str(datetime.now().date()),
                            "estimatedCompletion": None,
                            "enrollmentTarget": 0
                        }
                        await comp_client.add_trial(matched_comp_id, trial_payload, headers=headers)
                else:
                    logger.info(f"No competitor match for document {doc.id} (company: {company})")

                # 3. Create Insight
                # Ensure we send a YYYY-MM-DD string as expected by Pydantic 'date' field
                if doc.published_date:
                    published_date_str = doc.published_date.date().isoformat()
                else:
                    published_date_str = datetime.now().date().isoformat()
                
                insight_payload = {
                    "title": f"[{category}] {doc.title[:80]}", 
                    "description": description,
                    "category": category,
                    "therapeuticArea": therapeutic_area,
                    "impactLevel": impact_level,
                    "relevanceScore": relevance_score,
                    "source": doc.source,
                    "sourceDocumentId": doc.id,
                    "competitorId": matched_comp_id,
                    "publishedDate": published_date_str
                }
                
                insight_created = False
                async with httpx.AsyncClient() as client:
                    resp = await client.post(f"{INSIGHTS_SERVICE_URL}/api/insights", json=insight_payload, headers=headers)
                    if resp.status_code == 201:
                        insight_resp = resp.json()
                        logger.info(f"Created insight for doc {doc.id}")
                        insight_created = True
                    else:
                        logger.error(f"Failed to create insight: {resp.text}")

                if insight_created:
                    # 4. Trigger Notification (matches user subscriptions by therapeuticArea + competitorId)
                    if insight_resp.get("id"):
                        try:
                            notification_payload = {
                                 "insightId": insight_resp.get("id"),
                                 "title": insight_payload["title"],
                                 "description": summary,
                                 "therapeuticArea": therapeutic_area,
                                 "competitorId": matched_comp_id
                            }

                            async with httpx.AsyncClient() as client:
                                 # Internal trigger might require system/admin role or just authentication
                                 await client.post(f"{NOTIFICATION_SERVICE_URL}/api/notifications/trigger", json=notification_payload, headers=headers)
                                 logger.info(f"Triggered notification for insight {insight_resp.get('id')}")
                        except Exception as ne:
                            logger.error(f"Failed to trigger notification: {ne}")

                    # 5. Mark as Processed ONLY if insight was created
                    doc.processed = True
                    await session.commit()
                else:
                    logger.warning(f"Skipping processed=True for doc {doc.id} due to insight creation failure")
                
            except Exception as e:
                logger.error(f"Error processing doc {doc.id}: {e}")
                await session.rollback()
