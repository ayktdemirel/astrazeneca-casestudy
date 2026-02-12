from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CrawlJobCreate(BaseModel):
    source: str
    query: str
    schedule: Optional[str] = None
    enabled: bool = True

class CrawlJobUpdate(BaseModel):
    source: Optional[str] = None
    query: Optional[str] = None
    schedule: Optional[str] = None
    enabled: Optional[bool] = None

class CrawlJobResponse(CrawlJobCreate):
    id: str
    created_at: datetime = Field(serialization_alias="createdAt")

    class Config:
        from_attributes = True

class CrawlRunResponse(BaseModel):
    id: str
    job_id: str = Field(serialization_alias="jobId")
    status: str
    started_at: datetime = Field(serialization_alias="startedAt")
    finished_at: Optional[datetime] = Field(serialization_alias="finishedAt")

    class Config:
        from_attributes = True
