from sqlalchemy import Column, String, Boolean, DateTime, Text
from ..database import Base
from datetime import datetime
import uuid

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source = Column(String, nullable=False)
    external_id = Column(String, unique=True)
    url = Column(String)
    published_date = Column(DateTime)
    title = Column(String)
    raw_content = Column(Text) # JSON string or raw text
    processed = Column(Boolean, default=False)
    ingested_at = Column(DateTime, default=datetime.utcnow)
