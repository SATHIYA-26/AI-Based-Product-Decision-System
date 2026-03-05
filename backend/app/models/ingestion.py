"""Data ingestion models for storing raw reviews and ingestion metadata."""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()


class RawReview(Base):
    """Stores raw review data from any ingestion source."""
    
    __tablename__ = "raw_reviews"
    
    id = Column(Integer, primary_key=True)
    source = Column(String(50), nullable=False)  # "csv", "api", "play_store", etc.
    source_id = Column(String(100), nullable=True)  # external ID from source
    review_text = Column(Text, nullable=False)
    rating = Column(Float, nullable=True)  # 1-5 star rating if available
    author = Column(String(255), nullable=True)
    timestamp = Column(DateTime, nullable=True)  # when the review was posted
    extra_data = Column(String(1000), nullable=True)  # JSON for extra data
    is_duplicate = Column(Boolean, default=False)
    ingested_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "source": self.source,
            "source_id": self.source_id,
            "review_text": self.review_text,
            "rating": self.rating,
            "author": self.author,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "metadata": self.extra_data,
            "is_duplicate": self.is_duplicate,
            "ingested_at": self.ingested_at.isoformat() if self.ingested_at else None
        }


class IngestionJob(Base):
    """Tracks data ingestion jobs and their status."""
    
    __tablename__ = "ingestion_jobs"
    
    id = Column(Integer, primary_key=True)
    job_type = Column(String(50), nullable=False)  # "csv_upload", "api_import", "scheduled"
    source = Column(String(50), nullable=False)  # where data came from
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    total_records = Column(Integer, default=0)
    successful = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    duplicates_found = Column(Integer, default=0)
    error_message = Column(String(500), default="")
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "job_type": self.job_type,
            "source": self.source,
            "status": self.status,
            "total_records": self.total_records,
            "successful": self.successful,
            "failed": self.failed,
            "duplicates_found": self.duplicates_found,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


def get_ingestion_db_session(db_url: str = "sqlite:///./cluster_analysis.db"):
    """Factory to create a database session for ingestion data."""
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()
