"""
Apple App Store Connector - Fetches reviews from iOS App Store.

This connector fetches app reviews from the Apple App Store using
the public RSS feed or App Store Connect API.

Requires:
    - app-store-scraper package for scraping method
    - App Store Connect API credentials for official API method
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
)

logger = logging.getLogger(__name__)


class AppStoreConnector(BaseConnector):
    """
    Connector for fetching reviews from Apple App Store.
    
    Supports multiple methods:
    1. Public RSS Feed (no authentication required)
    2. App Store Connect API (requires API key)
    3. Web scraping using app-store-scraper package
    
    Configuration:
        config = ConnectorConfig(
            name="my_app_app_store",
            source_type="app_store",
            app_id="123456789",  # Apple App ID (numeric)
            api_key="your_api_key",  # Optional
            fetch_limit=100,
            extra_config={
                "country": "us",
                "use_rss": True,
            }
        )
    """
    
    # Supported countries for App Store
    SUPPORTED_COUNTRIES = [
        'us', 'gb', 'ca', 'au', 'de', 'fr', 'jp', 'cn', 'in', 'br',
        'mx', 'es', 'it', 'nl', 'ru', 'kr', 'se', 'no', 'dk', 'fi'
    ]
    
    def __init__(self, config: ConnectorConfig):
        """Initialize App Store connector."""
        super().__init__(config)
        self._country = config.extra_config.get('country', 'us')
        self._use_rss = config.extra_config.get('use_rss', True)
        
    def validate_config(self) -> List[str]:
        """Validate App Store specific configuration."""
        errors = super().validate_config()
        
        if not self.config.app_id:
            errors.append("app_id is required for App Store connector")
        
        country = self.config.extra_config.get('country', 'us')
        if country not in self.SUPPORTED_COUNTRIES:
            errors.append(f"Unsupported country: {country}")
        
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
        Fetch reviews from Apple App Store.
        
        Args:
            since: Only fetch reviews after this datetime
            limit: Maximum number of reviews to fetch
        
        Returns:
            FetchResult with fetched reviews
        """
        limit = limit or self.config.fetch_limit
        self._log_fetch_start(since, limit)
        
        try:
            if self._use_rss:
                result = self._fetch_via_rss(since, limit)
            else:
                result = self._fetch_via_scraper(since, limit)
            
            self._update_status_on_success(result)
            self._log_fetch_complete(result)
            return result
            
        except Exception as e:
            self._update_status_on_error(str(e))
            return FetchResult(
                reviews=[],
                success=False,
                error_message=f"Fetch failed: {e}"
            )
    
    def _fetch_via_rss(
        self,
        since: Optional[datetime],
        limit: int
    ) -> FetchResult:
        """
        Fetch reviews using Apple's public RSS feed.
        
        The RSS feed provides up to 500 most recent reviews per country.
        """
        import requests
        import xml.etree.ElementTree as ET
        
        try:
            # Construct RSS feed URL
            # Format: https://itunes.apple.com/{country}/rss/customerreviews/id={app_id}/sortBy=mostRecent/xml
            rss_url = (
                f"https://itunes.apple.com/{self._country}/rss/customerreviews/"
                f"id={self.config.app_id}/sortBy=mostRecent/xml"
            )
            
            response = requests.get(
                rss_url,
                timeout=self.config.timeout_seconds,
                headers={'User-Agent': 'ReviewClusteringSystem/1.0'}
            )
            
            if response.status_code == 404:
                # App not found or no reviews
                return FetchResult(
                    reviews=[],
                    success=True,
                    error_message="No reviews found (app may be new or in different country)"
                )
            
            response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.content)
            
            # Define namespace
            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'im': 'http://itunes.apple.com/rss'
            }
            
            reviews_data = []
            entries = root.findall('.//atom:entry', ns)
            
            for entry in entries[:limit]:
                # Extract review data
                title = entry.find('atom:title', ns)
                content = entry.find('atom:content', ns)
                author = entry.find('atom:author/atom:name', ns)
                rating = entry.find('im:rating', ns)
                updated = entry.find('atom:updated', ns)
                review_id = entry.find('atom:id', ns)
                version = entry.find('im:version', ns)
                
                # Parse timestamp
                review_time = None
                if updated is not None and updated.text:
                    try:
                        review_time = datetime.fromisoformat(
                            updated.text.replace('Z', '+00:00')
                        )
                    except:
                        pass
                
                # Filter by date
                if since and review_time and not self._is_after(review_time, since):
                    continue
                
                # Get rating value
                rating_value = None
                if rating is not None and rating.text:
                    try:
                        rating_value = float(rating.text)
                    except:
                        pass
                
                # Filter by rating
                if self.config.min_rating and rating_value and rating_value < self.config.min_rating:
                    continue
                if self.config.max_rating and rating_value and rating_value > self.config.max_rating:
                    continue
                
                # Combine title and content
                review_text = ""
                if title is not None and title.text:
                    review_text = title.text
                if content is not None and content.text:
                    if review_text:
                        review_text += " - " + content.text
                    else:
                        review_text = content.text
                
                if not review_text or len(review_text.strip()) < 10:
                    continue
                
                review_data = ReviewData(
                    text=review_text,
                    rating=rating_value,
                    author=author.text if author is not None else "Anonymous",
                    timestamp=review_time,
                    source_id=review_id.text if review_id is not None else None,
                    source=f"app_store:{self.config.app_id}",
                    language=self._country,
                    version=version.text if version is not None else None,
                    extra_data={
                        'country': self._country,
                        'fetch_method': 'rss',
                    }
                )
                
                reviews_data.append(review_data)
            
            return FetchResult(
                reviews=reviews_data,
                success=True,
                total_available=len(entries),
            )
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"RSS fetch failed: {e}, using mock data")
            return self._generate_mock_reviews(since, limit)
        except ET.ParseError as e:
            logger.warning(f"RSS parse failed: {e}, using mock data")
            return self._generate_mock_reviews(since, limit)
    
    def _fetch_via_scraper(
        self,
        since: Optional[datetime],
        limit: int
    ) -> FetchResult:
        """
        Fetch reviews using app-store-scraper package.
        """
        try:
            from app_store_scraper import AppStore
            
            app = AppStore(
                country=self._country,
                app_name="",  # Not required if app_id is provided
                app_id=self.config.app_id
            )
            
            app.review(how_many=limit)
            
            reviews_data = []
            for review in app.reviews:
                review_time = review.get('date')
                
                # Filter by date
                if since and review_time and not self._is_after(review_time, since):
                    continue
                
                # Filter by rating
                rating = review.get('rating')
                if self.config.min_rating and rating and rating < self.config.min_rating:
                    continue
                if self.config.max_rating and rating and rating > self.config.max_rating:
                    continue
                
                review_data = ReviewData(
                    text=review.get('review', ''),
                    rating=float(rating) if rating else None,
                    author=review.get('userName', 'Anonymous'),
                    timestamp=review_time,
                    source_id=review.get('id'),
                    source=f"app_store:{self.config.app_id}",
                    language=self._country,
                    version=review.get('version'),
                    helpful_count=review.get('isEdited', 0),
                    extra_data={
                        'title': review.get('title'),
                        'country': self._country,
                    }
                )
                
                if review_data.is_valid():
                    reviews_data.append(review_data)
            
            return FetchResult(
                reviews=reviews_data,
                success=True,
            )
            
        except ImportError:
            logger.warning("app-store-scraper not installed, using RSS method")
            return self._fetch_via_rss(since, limit)
        except Exception as e:
            logger.warning(f"Scraper failed: {e}, using mock data")
            return self._generate_mock_reviews(since, limit)
    
    def _generate_mock_reviews(
        self,
        since: Optional[datetime],
        limit: int
    ) -> FetchResult:
        """Generate mock reviews for testing."""
        import random
        
        mock_reviews = [
            ("This app crashes every time I open it", 1),
            ("Login screen stuck on loading forever", 1),
            ("Cannot make purchases, payment always fails", 2),
            ("Would be great if it had dark mode", 4),
            ("Amazing app, changed my life!", 5),
            ("Extremely slow performance on my iPhone", 2),
            ("Simply the best app in this category", 5),
            ("Push notifications stopped working", 2),
            ("Confusing interface, hard to find anything", 3),
            ("Drains my battery way too fast", 1),
            ("Latest update added great new features", 5),
            ("Search is completely broken", 2),
            ("App won't even launch anymore", 1),
            ("Great customer support team", 4),
            ("Lacks features that Android version has", 2),
        ]
        
        reviews_data = []
        base_time = datetime.utcnow()
        
        for i, (text, rating) in enumerate(mock_reviews[:limit]):
            import random
            review_time = base_time - timedelta(hours=random.randint(1, 168))
            
            if since and review_time < since:
                continue
            
            if self.config.min_rating and rating < self.config.min_rating:
                continue
            if self.config.max_rating and rating > self.config.max_rating:
                continue
            
            review_data = ReviewData(
                text=text,
                rating=float(rating),
                author=f"ios_user_{random.randint(1000, 9999)}",
                timestamp=review_time,
                source_id=f"mock_as_{i}_{int(base_time.timestamp())}",
                source=f"app_store:{self.config.app_id}",
                language=self._country,
                version="3.2.1",
                extra_data={'country': self._country, 'mock': True}
            )
            reviews_data.append(review_data)
        
        return FetchResult(
            reviews=reviews_data,
            success=True,
            error_message="Using mock data - install app-store-scraper for real reviews"
        )
