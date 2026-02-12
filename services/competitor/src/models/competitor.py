from sqlalchemy import Column, String, Date, ARRAY, Integer
from sqlalchemy.orm import relationship
from src.database import Base
from datetime import datetime

class Competitor(Base):
    __tablename__ = "competitors"

    id = Column(String, primary_key=True)  # Using String ID as per requirement ("comp-001")
    name = Column(String, nullable=False)
    headquarters = Column(String)
    therapeutic_areas = Column(ARRAY(String))
    active_drugs = Column(Integer, default=0)
    pipeline_drugs = Column(Integer, default=0)
    created_at = Column(Date, default=datetime.utcnow)

    trials = relationship("ClinicalTrial", back_populates="competitor")
