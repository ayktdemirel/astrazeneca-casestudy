from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import date

class InsightBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    therapeutic_area: Optional[str] = Field(default=None, alias="therapeuticArea")
    competitor_id: Optional[str] = Field(default=None, alias="competitorId")
    impact_level: Optional[str] = Field(default=None, alias="impactLevel")
    relevance_score: Optional[float] = Field(default=None, alias="relevanceScore")
    source: Optional[str] = None
    published_date: Optional[date] = Field(default=None, alias="publishedDate")
    source_document_id: Optional[str] = Field(default=None, alias="sourceDocumentId")
    
    model_config = ConfigDict(populate_by_name=True)

class InsightCreate(InsightBase):
    pass

class InsightUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    therapeutic_area: Optional[str] = Field(default=None, alias="therapeuticArea")
    competitor_id: Optional[str] = Field(default=None, alias="competitorId")
    impact_level: Optional[str] = Field(default=None, alias="impactLevel")
    relevance_score: Optional[float] = Field(default=None, alias="relevanceScore")
    source: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)

class InsightResponse(InsightBase):
    id: str
    created_at: Optional[date] = Field(default=None, alias="createdAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
