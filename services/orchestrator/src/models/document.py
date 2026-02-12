# We need the Document model to query it. 
# In a real microservice architecture, we shouldn't share models directly this coupling.
# Ideally, we would publish events "DocumentIngested" and listen to them.
# But per the requirement "tagging service automated in the db", we will access the table directly.

from sqlalchemy import Column, String, Boolean, Text, DateTime
from ..database import Base

class Document(Base):
    __tablename__ = "documents" # Mapping to the existing table created by Crawler

    id = Column(String, primary_key=True)
    source = Column(String)
    title = Column(String)
    raw_content = Column(Text)
    processed = Column(Boolean, default=False)
    published_date = Column(DateTime, nullable=True)
