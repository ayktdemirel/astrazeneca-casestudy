from sqlalchemy import Column, String, Date, Integer, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base
from datetime import datetime

class ClinicalTrial(Base):
    __tablename__ = "clinical_trials"

    id = Column(String, primary_key=True) # e.g. "trial-001"
    competitor_id = Column(String, ForeignKey("competitors.id"), nullable=False)
    trial_id = Column(String, nullable=False) # e.g. "NCT12345678"
    drug_name = Column(String, nullable=False)
    phase = Column(String)
    indication = Column(String)
    status = Column(String)
    start_date = Column(Date)
    estimated_completion = Column(Date)
    enrollment_target = Column(Integer)
    created_at = Column(Date, default=datetime.utcnow)

    competitor = relationship("Competitor", back_populates="trials")
