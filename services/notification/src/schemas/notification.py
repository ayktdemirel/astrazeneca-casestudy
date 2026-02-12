from pydantic import BaseModel, Field, model_validator
from typing import Optional
from datetime import datetime

class NotificationSendRequest(BaseModel):
    insightId: str
    subscriptionId: str

class TriggerNotificationRequest(BaseModel):
    title: str
    description: Optional[str] = None
    therapeutic_area: Optional[str] = Field(default=None, alias="therapeuticArea")
    competitor_id: Optional[str] = Field(default=None, alias="competitorId")
    insight_id: str = Field(alias="insightId")

class NotificationHistoryResponse(BaseModel):
    id: str
    user_id: str = Field(serialization_alias="userId")
    subscription_id: Optional[str] = Field(default=None, serialization_alias="subscriptionId")
    insight_id: str = Field(serialization_alias="insightId")
    status: str
    sent_at: datetime = Field(serialization_alias="sentAt")
    read: bool
    payload: Optional[dict] = Field(default=None, validation_alias="payload_json")
    message: Optional[str] = None

    @model_validator(mode='after')
    def extract_message(self):
        if not self.message and self.payload and "message" in self.payload:
            self.message = self.payload["message"]
        return self

    class Config:
        from_attributes = True

