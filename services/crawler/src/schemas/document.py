from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class DocumentResponse(BaseModel):
    id: str
    source: str
    external_id: Optional[str] = Field(serialization_alias="externalId")
    title: Optional[str]
    url: Optional[str]
    published_date: Optional[datetime] = Field(serialization_alias="publishedDate")
    ingested_at: datetime = Field(serialization_alias="ingestedAt")
    processed: bool

    class Config:
        from_attributes = True
