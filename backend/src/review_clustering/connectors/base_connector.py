"""
Base Connector - Abstract interface for all external review API connectors.

This module defines the contract that all connectors must implement,
ensuring consistent behavior and data format across different review sources.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ConnectorStatus(Enum):
    """Status of a connector."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"


@dataclass
class ReviewData:
    """
    Standardized review data structure.
    
    All connectors must convert their source-specific review format
    into this unified structure for processing by the pipeline.
    """
    text: str                                    # Review text content
    rating: Optional[float] = None               # Star rating (1-5 scale)
    author: Optional[str] = None                 # Reviewer name/username
    timestamp: Optional[datetime] = None         # When review was posted
    source_id: Optional[str] = None              # Unique ID from source
    source: str = "unknown"                      # Source identifier
    language: Optional[str] = None               # Review language code
    version: Optional[str] = None                # App version reviewed
    device: Optional[str] = None                 # Device type/model
    helpful_count: Optional[int] = None          # Upvotes/helpful votes
    reply: Optional[str] = None                  # Developer reply if any
    extra_data: Dict[str, Any] = field(default_factory=dict)  # Additional metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            "review_text": self.text,
            "rating": self.rating,
            "author": self.author,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "source_id": self.source_id,
            "source": self.source,
            "language": self.language,
            "version": self.version,
            "device": self.device,
            "helpful_count": self.helpful_count,
            "reply": self.reply,
            "extra_data": self.extra_data,
        }
    
    def is_valid(self) -> bool:
        """Check if review has minimum required data."""
        return bool(self.text and len(self.text.strip()) >= 10)


@dataclass
class ConnectorConfig:
    """
    Configuration for a connector instance.
    
    Provides all settings needed to connect to and fetch from an external API.
    """
    name: str                                    # Connector identifier
    source_type: str                             # Type of source (google_play, app_store, api)
    enabled: bool = True                         # Whether connector is active
    
    # API Configuration
    api_endpoint: Optional[str] = None           # Base API URL
    api_key: Optional[str] = None                # API authentication key
    api_secret: Optional[str] = None             # API secret (if needed)
    
    # App/Product Configuration
    app_id: Optional[str] = None                 # Application ID (for app stores)
    product_id: Optional[str] = None             # Product ID (for internal APIs)
    
    # Fetch Configuration
    fetch_limit: int = 100                       # Max reviews per fetch
    fetch_interval_minutes: int = 60             # How often to fetch
    lookback_days: int = 7                       # How far back to fetch
    
    # Rate Limiting
    rate_limit_requests: int = 100               # Max requests per window
    rate_limit_window_seconds: int = 60          # Rate limit window
    
    # Filtering
    min_rating: Optional[float] = None           # Only fetch reviews >= rating
    max_rating: Optional[float] = None           # Only fetch reviews <= rating
    languages: List[str] = field(default_factory=list)  # Language filters
    
    # Authentication
    auth_type: str = "none"                      # none, api_key, oauth, basic
    auth_header: Optional[str] = None            # Custom auth header name
    
    # Request Configuration
    timeout_seconds: int = 30                    # Request timeout
    retry_attempts: int = 3                      # Number of retries
    retry_delay_seconds: int = 5                 # Delay between retries
    
    # Additional settings
    extra_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FetchResult:
    """
    Result of a fetch operation.
    
    Contains the fetched reviews along with metadata about the fetch operation.
    """
    reviews: List[ReviewData]                    # Fetched reviews
    success: bool = True                         # Whether fetch succeeded
    error_message: Optional[str] = None          # Error description if failed
    fetch_timestamp: datetime = field(default_factory=datetime.utcnow)
    total_available: Optional[int] = None        # Total reviews available
    next_page_token: Optional[str] = None        # For pagination
    rate_limit_remaining: Optional[int] = None   # Remaining API quota
    
    @property
    def count(self) -> int:
        """Number of reviews fetched."""
        return len(self.reviews)


class BaseConnector(ABC):
    """
    Abstract base class for all review API connectors.
    
    Provides the interface that all connectors must implement,
    along with common utility methods for logging, error handling, etc.
    
    Usage:
        class MyConnector(BaseConnector):
            def fetch_reviews(self, since=None, limit=100):
                # Implementation
                pass
            
            def test_connection(self):
                # Implementation
                pass
    """
    
    def __init__(self, config: ConnectorConfig):
        """
        Initialize connector with configuration.
        
        Args:
            config: ConnectorConfig instance with all settings
        """
        self.config = config
        self.status = ConnectorStatus.INACTIVE
        self.last_fetch: Optional[datetime] = None
        self.last_error: Optional[str] = None
        self.total_fetched: int = 0
        self._logger = logging.getLogger(f"{__name__}.{config.name}")
    
    @property
    def name(self) -> str:
        """Get connector name."""
        return self.config.name
    
    @property
    def source_type(self) -> str:
        """Get source type."""
        return self.config.source_type
    
    @property
    def is_enabled(self) -> bool:
        """Check if connector is enabled."""
        return self.config.enabled and self.status != ConnectorStatus.ERROR
    
    @abstractmethod
    def fetch_reviews(
        self,
        since: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> FetchResult:
        """
        Fetch reviews from the external source.
        
        Args:
            since: Only fetch reviews posted after this datetime
            limit: Maximum number of reviews to fetch (defaults to config.fetch_limit)
        
        Returns:
            FetchResult containing the fetched reviews and metadata
        
        Raises:
            ConnectionError: If unable to connect to the API
            AuthenticationError: If authentication fails
            RateLimitError: If rate limit is exceeded
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test the connection to the external API.
        
        Returns:
            True if connection is successful, False otherwise
        """
        pass
    
    def validate_config(self) -> List[str]:
        """
        Validate the connector configuration.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if not self.config.name:
            errors.append("Connector name is required")
        
        if not self.config.source_type:
            errors.append("Source type is required")
        
        return errors
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current connector status.
        
        Returns:
            Dictionary with status information
        """
        return {
            "name": self.name,
            "source_type": self.source_type,
            "status": self.status.value,
            "enabled": self.is_enabled,
            "last_fetch": self.last_fetch.isoformat() if self.last_fetch else None,
            "last_error": self.last_error,
            "total_fetched": self.total_fetched,
        }
    
    def _log_fetch_start(self, since: Optional[datetime], limit: int):
        """Log the start of a fetch operation."""
        self._logger.info(
            f"Starting fetch: since={since}, limit={limit}"
        )
    
    def _log_fetch_complete(self, result: FetchResult):
        """Log the completion of a fetch operation."""
        if result.success:
            self._logger.info(
                f"Fetch complete: {result.count} reviews fetched"
            )
        else:
            self._logger.error(
                f"Fetch failed: {result.error_message}"
            )
    
    def _update_status_on_success(self, result: FetchResult):
        """Update connector status after successful fetch."""
        self.status = ConnectorStatus.ACTIVE
        self.last_fetch = result.fetch_timestamp
        self.last_error = None
        self.total_fetched += result.count
    
    def _update_status_on_error(self, error: str):
        """Update connector status after failed fetch."""
        self.status = ConnectorStatus.ERROR
        self.last_error = error
        self._logger.error(f"Connector error: {error}")

    @staticmethod
    def _normalize_dt(dt: datetime) -> datetime:
        """Normalize any datetime to naive UTC.
        
        If timezone-aware, convert to UTC then strip tzinfo.
        If already naive, assume it's UTC and return as-is.
        """
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt

    @staticmethod
    def _is_after(review_time: datetime, since: datetime) -> bool:
        """Compare two datetimes safely by normalizing both to naive UTC."""
        return BaseConnector._normalize_dt(review_time) >= BaseConnector._normalize_dt(since)


class ConnectorError(Exception):
    """Base exception for connector errors."""
    pass


class AuthenticationError(ConnectorError):
    """Raised when API authentication fails."""
    pass


class RateLimitError(ConnectorError):
    """Raised when API rate limit is exceeded."""
    pass


class ConfigurationError(ConnectorError):
    """Raised when connector configuration is invalid."""
    pass
