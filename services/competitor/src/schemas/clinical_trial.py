from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class ClinicalTrialBase(BaseModel):
    trialId: str
    drugName: str
    phase: Optional[str] = None
    indication: Optional[str] = None
    status: Optional[str] = None
    startDate: Optional[date] = None
    estimatedCompletion: Optional[date] = None
    enrollmentTarget: Optional[int] = None

class ClinicalTrialCreate(ClinicalTrialBase):
    pass

class ClinicalTrialResponse(BaseModel):
    id: str
    competitor_id: str = Field(serialization_alias="competitorId")
    trial_id: str = Field(serialization_alias="trialId")
    drug_name: str = Field(serialization_alias="drugName")
    phase: Optional[str] = None
    indication: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[date] = Field(default=None, serialization_alias="startDate")
    estimated_completion: Optional[date] = Field(default=None, serialization_alias="estimatedCompletion")
    enrollment_target: Optional[int] = Field(default=None, serialization_alias="enrollmentTarget")
    created_at: Optional[date] = Field(default=None, serialization_alias="createdAt")

    class Config:
        from_attributes = True
