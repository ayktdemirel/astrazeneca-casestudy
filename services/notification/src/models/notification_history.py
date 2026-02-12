from sqlalchemy import Column, String, Boolean, DateTime, JSON, ForeignKey
from src.database import Base
from datetime import datetime

class NotificationHistory(Base):
    __tablename__ = "notification_history"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    subscription_id = Column(String, ForeignKey("subscriptions.id"))
    insight_id = Column(String, nullable=False)
    status = Column(String) # SENT, FAILED
    payload_json = Column(JSON)
    correlation_id = Column(String)
    read = Column(Boolean, default=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
