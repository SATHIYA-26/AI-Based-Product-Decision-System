"""Database models for storing cluster analysis results."""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

Base = declarative_base()


class ClusterResult(Base):
    """Stores a cluster analysis run and its results."""
    
    __tablename__ = "cluster_results"
    
    id = Column(Integer, primary_key=True)
    run_id = Column(String(36), nullable=False)  # UUID for the pipeline run (multiple clusters per run)
    cluster_id = Column(Integer, nullable=False)
    frequency = Column(Integer, nullable=False)
    avg_sentiment = Column(Float, nullable=False)
    priority_score = Column(Float, nullable=False)
    trend_score = Column(Float, nullable=False)
    summary = Column(String(500), default="")
    label = Column(String(50), default="")
    representative_reviews = Column(JSON, nullable=True)  # Store as JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "run_id": self.run_id,
            "cluster_id": self.cluster_id,
            "frequency": self.frequency,
            "avg_sentiment": self.avg_sentiment,
            "priority_score": self.priority_score,
            "trend_score": self.trend_score,
            "summary": self.summary,
            "label": self.label,
            "representative_reviews": self.representative_reviews,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class PipelineRun(Base):
    """Records metadata about a full pipeline execution."""
    
    __tablename__ = "pipeline_runs"
    
    id = Column(Integer, primary_key=True)
    run_id = Column(String(36), unique=True, nullable=False)  # UUID
    num_inputs = Column(Integer, nullable=False)
    num_cleaned = Column(Integer, nullable=False)
    num_clusters = Column(Integer, nullable=False)
    status = Column(String(20), default="completed")  # completed, failed, etc.
    error_message = Column(String(500), default="")
    execution_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "run_id": self.run_id,
            "num_inputs": self.num_inputs,
            "num_cleaned": self.num_cleaned,
            "num_clusters": self.num_clusters,
            "status": self.status,
            "error_message": self.error_message,
            "execution_time_ms": self.execution_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


def get_db_session(db_url: str = "sqlite:///./cluster_analysis.db"):
    """Factory to create a database session.
    
    Args:
        db_url: Database connection string. Defaults to SQLite file.
                For production, use: "postgresql://user:pass@localhost/dbname"
    """
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()
