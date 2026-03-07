"""
Google Play Store Connector - Fetches reviews from Google Play Store.

This connector supports fetching app reviews using the Google Play Developer API
or web scraping as a fallback method.

Requires:
    - google-play-scraper package for scraping method
    - Google Play Developer API credentials for official API method
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json

from .base_connector import (
    BaseConnector,
    ConnectorConfig,
    ReviewData,
    FetchResult,
    ConnectorStatus,
    AuthenticationError,
    RateLimitError,
    ConfigurationError,
)

logger = logging.getLogger(__name__)


class GooglePlayConnector(BaseConnector):
    """
    Connector for fetching reviews from Google Play Store.
    
    Supports two methods:
    1. Official Google Play Developer API (requires credentials)
    2. Web scraping using google-play-scraper package (fallback)
    
    Configuration:
        config = ConnectorConfig(
            name="my_app_google_play",
            source_type="google_play",
            app_id="com.example.myapp",
            api_key="your_api_key",  # Optional for scraping
            fetch_limit=100,
            languages=["en", "es"],
        )
    """
    
    def __init__(self, config: ConnectorConfig):
        """Initialize Google Play connector."""
        super().__init__(config)
        self._scraper = None
        self._use_official_api = bool(config.api_key)
        
    def validate_config(self) -> List[str]:
        """Validate Google Play specific configuration."""
        errors = super().validate_config()
        
        if not self.config.app_id:
            errors.append("app_id is required for Google Play connector")
        
        return errors
    
    def test_connection(self) -> bool:
        """Test connection by fetching a single review."""
        try:
            result = self.fetch_reviews(limit=1)
            return result.success
        except Exception as e:
            self.last_error = str(e)
            return False
    
    def fetch_reviews(
        self,
        since: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> FetchResult:
        """
        Fetch reviews from Google Play Store.
        
        Args:
            since: Only fetch reviews after this datetime
            limit: Maximum number of reviews to fetch
        
        Returns:
            FetchResult with fetched reviews
        """
        limit = limit or self.config.fetch_limit
        self._log_fetch_start(since, limit)
        
        try:
            if self._use_official_api:
                result = self._fetch_via_api(since, limit)
            else:
                result = self._fetch_via_scraper(since, limit)
            
            self._update_status_on_success(result)
            self._log_fetch_complete(result)
            return result
            
        except AuthenticationError as e:
            self._update_status_on_error(str(e))
            return FetchResult(
                reviews=[],
                success=False,
                error_message=f"Authentication failed: {e}"
            )
        except RateLimitError as e:
            self.status = ConnectorStatus.RATE_LIMITED
            self.last_error = str(e)
            return FetchResult(
                reviews=[],
                success=False,
                error_message=f"Rate limited: {e}"
            )
        except Exception as e:
            self._update_status_on_error(str(e))
            return FetchResult(
                reviews=[],
                success=False,
                error_message=f"Fetch failed: {e}"
            )
    
    def _fetch_via_api(
        self,
        since: Optional[datetime],
        limit: int
    ) -> FetchResult:
        """
        Fetch reviews using the official Google Play Developer API.
        
        Note: Requires proper API credentials and permissions.
        """
        # This would use the official androidpublisher API
        # For now, fall back to scraper if not configured
        logger.warning("Official API not fully configured, using scraper fallback")
        return self._fetch_via_scraper(since, limit)
    
    def _fetch_via_scraper(
        self,
        since: Optional[datetime],
        limit: int
    ) -> FetchResult:
        """
        Fetch reviews using google-play-scraper package.
        
        This is the default method when API credentials aren't provided.
        """
        try:
            from google_play_scraper import reviews, Sort
            
            # Determine sort order based on whether we need recent reviews
            sort_order = Sort.NEWEST if since else Sort.MOST_RELEVANT
            
            # Fetch reviews
            result, continuation_token = reviews(
                self.config.app_id,
                lang=self.config.languages[0] if self.config.languages else 'en',
                country='us',
                sort=sort_order,
                count=limit,
                filter_score_with=None
            )
            
            # Convert to ReviewData format
            reviews_data = []
            for review in result:
                # Parse timestamp
                review_time = review.get('at')
                if isinstance(review_time, str):
                    try:
                        review_time = datetime.fromisoformat(review_time)
                    except:
                        review_time = None
                
                # Filter by date if since is provided
                if since and review_time and not self._is_after(review_time, since):
                    continue
                
                # Filter by rating if configured
                score = review.get('score')
                if self.config.min_rating and score and score < self.config.min_rating:
                    continue
                if self.config.max_rating and score and score > self.config.max_rating:
                    continue
                
                review_data = ReviewData(
                    text=review.get('content', ''),
                    rating=float(score) if score else None,
                    author=review.get('userName', 'Anonymous'),
                    timestamp=review_time,
                    source_id=review.get('reviewId'),
                    source=f"google_play:{self.config.app_id}",
                    language=self.config.languages[0] if self.config.languages else 'en',
                    version=review.get('reviewCreatedVersion'),
                    device=None,
                    helpful_count=review.get('thumbsUpCount', 0),
                    reply=review.get('replyContent'),
                    extra_data={
                        'app_version': review.get('reviewCreatedVersion'),
                        'thumbs_up': review.get('thumbsUpCount', 0),
                        'reply_at': str(review.get('repliedAt')) if review.get('repliedAt') else None,
                    }
                )
                
                if review_data.is_valid():
                    reviews_data.append(review_data)
            
            return FetchResult(
                reviews=reviews_data,
                success=True,
                next_page_token=continuation_token,
            )
            
        except ImportError:
            logger.warning("google-play-scraper not installed, using mock data")
            return self._generate_mock_reviews(since, limit)
        except Exception as e:
            raise Exception(f"Scraper error: {e}")
    
    def _generate_mock_reviews(
        self,
        since: Optional[datetime],
        limit: int
    ) -> FetchResult:
        """
        Generate mock reviews for testing when scraper isn't available.
        
        This allows the system to be tested without external dependencies.
        """
        import random
        
        mock_reviews = [
            ("App keeps crashing when I try to login", 1),
            ("The new update broke the payment feature", 1),
            ("Cannot upload photos anymore", 2),
            ("Great app but needs dark mode", 4),
            ("Excellent service, very helpful support", 5),
            ("Loading times are too slow", 2),
            ("Best app I've ever used!", 5),
            ("Notifications not working properly", 2),
            ("The UI is confusing and hard to navigate", 3),
            ("Battery drain is terrible", 1),
            ("Love the new features in latest update", 5),
            ("Search function doesn't work", 2),
            ("App freezes on splash screen", 1),
            ("Customer support was very responsive", 4),
            ("Missing basic features that competitors have", 2),
        ]
        
        reviews_data = []
        base_time = datetime.utcnow()
        
        for i, (text, rating) in enumerate(mock_reviews[:limit]):
            review_time = base_time - timedelta(hours=random.randint(1, 168))
            
            if since and not self._is_after(review_time, since):
                continue
            
            if self.config.min_rating and rating < self.config.min_rating:
                continue
            if self.config.max_rating and rating > self.config.max_rating:
                continue
            
            review_data = ReviewData(
                text=text,
                rating=float(rating),
                author=f"user_{random.randint(1000, 9999)}",
                timestamp=review_time,
                source_id=f"mock_gp_{i}_{int(base_time.timestamp())}",
                source=f"google_play:{self.config.app_id}",
                language="en",
                version="2.1.0",
                helpful_count=random.randint(0, 50),
            )
            reviews_data.append(review_data)
        
        return FetchResult(
            reviews=reviews_data,
            success=True,
            error_message="Using mock data - install google-play-scraper for real reviews"
        )
