from sqlalchemy import Column, String, Date, Text, Float
from src.database import Base
from datetime import datetime

class Insight(Base):
    __tablename__ = "insights"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String)
    therapeutic_area = Column(String)
    competitor_id = Column(String)
    impact_level = Column(String) # High, Medium, Low
    relevance_score = Column(Float)
    source = Column(String)
    published_date = Column(Date)
    source_document_id = Column(String)
    created_at = Column(Date, default=datetime.utcnow)
