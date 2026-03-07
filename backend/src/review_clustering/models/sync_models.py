"""
Database models for automated review synchronization.

Contains models for:
- SyncJob: Records of synchronization job executions
- ConnectorConfiguration: Stored connector settings
- SyncSchedule: Scheduling configuration for connectors
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, Boolean, JSON, 
    create_engine, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum
import json

Base = declarative_base()


class SyncStatus(enum.Enum):
    """Status of a sync job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ConnectorType(enum.Enum):
    """Types of review source connectors."""
    GOOGLE_PLAY = "google_play"
    APP_STORE = "app_store"
    GENERIC_API = "api"
    CUSTOM = "custom"


class ConnectorConfiguration(Base):
    """
    Stores connector configurations in the database.
    
    Allows connectors to be configured via API/UI without code changes.
    """
    __tablename__ = "connector_configurations"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    connector_type = Column(String(50), nullable=False)
    enabled = Column(Boolean, default=True)
    
    # API Configuration
    api_endpoint = Column(String(500), nullable=True)
    api_key_encrypted = Column(String(500), nullable=True)  # Store encrypted
    
    # App/Product Configuration
    app_id = Column(String(255), nullable=True)
    product_id = Column(String(255), nullable=True)
    
    # Fetch Configuration
    fetch_limit = Column(Integer, default=100)
    fetch_interval_minutes = Column(Integer, default=60)
    lookback_days = Column(Integer, default=7)
    
    # Filtering
    min_rating = Column(Float, nullable=True)
    max_rating = Column(Float, nullable=True)
    languages = Column(JSON, default=list)
    
    # Additional configuration as JSON
    extra_config = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sync_jobs = relationship("SyncJob", back_populates="connector_config")
    
    def to_dict(self) -> dict:
        """Convert to dictionary (excludes sensitive data)."""
        return {
            "id": self.id,
            "name": self.name,
            "connector_type": self.connector_type,
            "enabled": self.enabled,
            "api_endpoint": self.api_endpoint,
            "app_id": self.app_id,
            "product_id": self.product_id,
            "fetch_limit": self.fetch_limit,
            "fetch_interval_minutes": self.fetch_interval_minutes,
            "lookback_days": self.lookback_days,
            "min_rating": self.min_rating,
            "max_rating": self.max_rating,
            "languages": self.languages,
            "extra_config": self.extra_config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def to_connector_config(self):
        """Convert to ConnectorConfig object for use with connectors."""
        from review_clustering.connectors.base_connector import ConnectorConfig
        
        return ConnectorConfig(
            name=self.name,
            source_type=self.connector_type,
            enabled=self.enabled,
            api_endpoint=self.api_endpoint,
            api_key=self.api_key_encrypted,  # Would need decryption in production
            app_id=self.app_id,
            product_id=self.product_id,
            fetch_limit=self.fetch_limit,
            fetch_interval_minutes=self.fetch_interval_minutes,
            lookback_days=self.lookback_days,
            min_rating=self.min_rating,
            max_rating=self.max_rating,
            languages=self.languages or [],
            extra_config=self.extra_config or {},
        )


class SyncJob(Base):
    """
    Records synchronization job executions.
    
    Provides audit trail and metrics for all sync operations.
    """
    __tablename__ = "sync_jobs"
    
    id = Column(Integer, primary_key=True)
    job_id = Column(String(36), unique=True, nullable=False)  # UUID
    
    # Connector reference
    connector_config_id = Column(Integer, ForeignKey("connector_configurations.id"), nullable=True)
    connector_name = Column(String(100), nullable=False)
    source_type = Column(String(50), nullable=False)
    
    # Status
    status = Column(String(20), default="pending")
    error_message = Column(Text, nullable=True)
    warnings = Column(JSON, default=list)
    
    # Timing
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Fetch metrics
    reviews_fetched = Column(Integer, default=0)
    reviews_valid = Column(Integer, default=0)
    reviews_duplicate = Column(Integer, default=0)
    reviews_stored = Column(Integer, default=0)
    
    # Pipeline metrics
    pipeline_triggered = Column(Boolean, default=False)
    pipeline_run_id = Column(String(36), nullable=True)
    clusters_created = Column(Integer, default=0)
    
    # Relationship
    connector_config = relationship("ConnectorConfiguration", back_populates="sync_jobs")
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        duration = None
        if self.completed_at and self.started_at:
            duration = (self.completed_at - self.started_at).total_seconds()
        
        return {
            "id": self.id,
            "job_id": self.job_id,
            "connector_name": self.connector_name,
            "source_type": self.source_type,
            "status": self.status,
            "error_message": self.error_message,
            "warnings": self.warnings,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": duration,
            "reviews_fetched": self.reviews_fetched,
            "reviews_valid": self.reviews_valid,
            "reviews_duplicate": self.reviews_duplicate,
            "reviews_stored": self.reviews_stored,
            "pipeline_triggered": self.pipeline_triggered,
            "pipeline_run_id": self.pipeline_run_id,
            "clusters_created": self.clusters_created,
        }


class SyncSchedule(Base):
    """
    Scheduling configuration for automated synchronization.
    
    Defines when and how often each connector should sync.
    """
    __tablename__ = "sync_schedules"
    
    id = Column(Integer, primary_key=True)
    connector_name = Column(String(100), nullable=False)
    
    # Schedule configuration
    enabled = Column(Boolean, default=True)
    cron_expression = Column(String(100), nullable=True)  # For cron-style scheduling
    interval_minutes = Column(Integer, default=60)  # For interval-based scheduling
    
    # Execution window (optional)
    start_hour = Column(Integer, nullable=True)  # 0-23, start of execution window
    end_hour = Column(Integer, nullable=True)    # 0-23, end of execution window
    days_of_week = Column(JSON, default=list)    # [0-6], 0=Monday
    
    # Last execution tracking
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    last_run_status = Column(String(20), nullable=True)
    consecutive_failures = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "connector_name": self.connector_name,
            "enabled": self.enabled,
            "cron_expression": self.cron_expression,
            "interval_minutes": self.interval_minutes,
            "start_hour": self.start_hour,
            "end_hour": self.end_hour,
            "days_of_week": self.days_of_week,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
            "last_run_status": self.last_run_status,
            "consecutive_failures": self.consecutive_failures,
        }


# Database session factory
def get_sync_db_session(db_url: str = "sqlite:///data/cluster_analysis.db"):
    """Create a database session for sync models."""
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


# Helper functions
def save_sync_job(result, connector_config_id: int = None) -> SyncJob:
    """
    Save a SyncJobResult to the database.
    
    Args:
        result: SyncJobResult from sync operation
        connector_config_id: Optional database ID of connector configuration
    
    Returns:
        SyncJob database record
    """
    session = get_sync_db_session()
    
    try:
        job = SyncJob(
            job_id=result.job_id,
            connector_config_id=connector_config_id,
            connector_name=result.connector_name,
            source_type=result.source_type,
            status="completed" if result.success else "failed",
            error_message=result.error_message,
            warnings=result.warnings,
            started_at=result.started_at,
            completed_at=result.completed_at,
            reviews_fetched=result.reviews_fetched,
            reviews_valid=result.reviews_valid,
            reviews_duplicate=result.reviews_duplicate,
            reviews_stored=result.reviews_stored,
            pipeline_triggered=result.pipeline_triggered,
            pipeline_run_id=result.pipeline_run_id,
            clusters_created=result.clusters_created,
        )
        
        session.add(job)
        session.commit()
        
        return job
        
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def get_sync_jobs(
    connector_name: str = None,
    status: str = None,
    limit: int = 100
) -> list:
    """
    Query sync jobs from the database.
    
    Args:
        connector_name: Filter by connector name
        status: Filter by status
        limit: Maximum records to return
    
    Returns:
        List of SyncJob dictionaries
    """
    session = get_sync_db_session()
    
    try:
        query = session.query(SyncJob)
        
        if connector_name:
            query = query.filter(SyncJob.connector_name == connector_name)
        if status:
            query = query.filter(SyncJob.status == status)
        
        query = query.order_by(SyncJob.started_at.desc()).limit(limit)
        
        return [job.to_dict() for job in query.all()]
        
    finally:
        session.close()


def get_connector_configs(enabled_only: bool = False) -> list:
    """
    Get all connector configurations from database.
    
    Args:
        enabled_only: Only return enabled connectors
    
    Returns:
        List of ConnectorConfiguration dictionaries
    """
    session = get_sync_db_session()
    
    try:
        query = session.query(ConnectorConfiguration)
        
        if enabled_only:
            query = query.filter(ConnectorConfiguration.enabled == True)
        
        return [config.to_dict() for config in query.all()]
        
    finally:
        session.close()


def save_connector_config(config_data: dict) -> ConnectorConfiguration:
    """
    Save or update a connector configuration.
    
    Args:
        config_data: Dictionary with configuration values
    
    Returns:
        ConnectorConfiguration database record
    """
    session = get_sync_db_session()
    
    try:
        # Check if exists
        existing = session.query(ConnectorConfiguration).filter(
            ConnectorConfiguration.name == config_data.get('name')
        ).first()
        
        if existing:
            # Update existing
            for key, value in config_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            config = existing
        else:
            # Create new
            config = ConnectorConfiguration(**config_data)
            session.add(config)
        
        session.commit()
        session.refresh(config)
        
        return config
        
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
