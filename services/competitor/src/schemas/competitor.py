from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class CompetitorBase(BaseModel):
    name: str
    headquarters: Optional[str] = None
    therapeuticAreas: Optional[List[str]] = []
    activeDrugs: Optional[int] = 0
    pipelineDrugs: Optional[int] = 0

class CompetitorCreate(CompetitorBase):
    pass

class CompetitorResponse(BaseModel):
    id: str
    name: str
    headquarters: Optional[str] = None
    therapeutic_areas: Optional[List[str]] = Field(default=[], serialization_alias="therapeuticAreas")
    active_drugs: Optional[int] = Field(default=0, serialization_alias="activeDrugs")
    pipeline_drugs: Optional[int] = Field(default=0, serialization_alias="pipelineDrugs")
    created_at: Optional[date] = Field(default=None, serialization_alias="createdAt")

    class Config:
        from_attributes = True
