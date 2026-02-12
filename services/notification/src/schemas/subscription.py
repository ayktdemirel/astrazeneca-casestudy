from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class SubscriptionBase(BaseModel):
    therapeuticAreas: Optional[List[str]] = []
    competitorIds: Optional[List[str]] = []
    channels: List[str]

class SubscriptionCreate(SubscriptionBase):
    pass

class SubscriptionResponse(BaseModel):
    id: str
    user_id: str = Field(serialization_alias="userId")
    therapeutic_areas: Optional[List[str]] = Field(default=[], serialization_alias="therapeuticAreas")
    competitor_ids: Optional[List[str]] = Field(default=[], serialization_alias="competitorIds")
    channels: List[str]
    created_at: datetime = Field(serialization_alias="createdAt")

    class Config:
        from_attributes = True
