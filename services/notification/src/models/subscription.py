from sqlalchemy import Column, String, ARRAY, DateTime
from src.database import Base
from datetime import datetime

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False) # In real app, this comes from auth token
    therapeutic_areas = Column(ARRAY(String))
    competitor_ids = Column(ARRAY(String))
    channels = Column(ARRAY(String)) # e.g. ["console", "email"]
    created_at = Column(DateTime, default=datetime.utcnow)
