from sqlalchemy import Column, String, Boolean, DateTime, JSON, ForeignKey
from ..database import Base
from datetime import datetime
import uuid

class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source = Column(String, nullable=False) # ClinicalTrials, FDA, Patents
    query = Column(String, nullable=False)
    schedule = Column(String) # Cron expression
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class CrawlRun(Base):
    __tablename__ = "crawl_runs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("crawl_jobs.id"))
    status = Column(String) # STARTED, COMPLETED, FAILED
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime)
    stats_json = Column(JSON)
