"""
Generic API Connector - Fetches reviews from custom REST APIs.

This connector provides a flexible way to connect to any REST API that
provides review data. It supports various authentication methods and
can be configured to map custom JSON fields to the internal review format.

Use cases:
- Internal product review databases
- Customer support systems (Zendesk, Freshdesk)
- Survey platforms (SurveyMonkey, Typeform)
- Social media APIs (Twitter, Reddit)
- Custom review aggregation services
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Callable
import json

import requests
from requests.auth import HTTPBasicAuth

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


class GenericAPIConnector(BaseConnector):
    """
    Generic connector for custom REST APIs.
    
    Highly configurable connector that can adapt to various API formats.
    Uses field mapping to convert custom JSON responses to ReviewData format.
    
    Configuration:
        config = ConnectorConfig(
            name="internal_reviews",
            source_type="api",
            api_endpoint="https://api.example.com/reviews",
            api_key="your_api_key",
            auth_type="api_key",  # none, api_key, bearer, basic, oauth
            auth_header="X-API-Key",  # Custom header for api_key auth
            fetch_limit=100,
            extra_config={
                "field_mapping": {
                    "text": "review_content",
                    "rating": "star_rating",
                    "author": "user.username",
                    "timestamp": "created_at",
                    "source_id": "id",
                },
                "response_path": "data.reviews",  # JSON path to reviews array
                "pagination": {
                    "type": "offset",  # offset, cursor, page
                    "limit_param": "limit",
                    "offset_param": "offset",
                },
                "date_format": "%Y-%m-%dT%H:%M:%SZ",
            }
        )
    """
    
    def __init__(self, config: ConnectorConfig):
        """Initialize Generic API connector."""
        super().__init__(config)
        
        # Extract configuration
        self._field_mapping = config.extra_config.get('field_mapping', {})
        self._response_path = config.extra_config.get('response_path', '')
        self._pagination = config.extra_config.get('pagination', {})
        self._date_format = config.extra_config.get('date_format', '%Y-%m-%dT%H:%M:%SZ')
        self._headers = config.extra_config.get('headers', {})
        self._params = config.extra_config.get('params', {})
        
        # Default field mapping if not provided
        if not self._field_mapping:
            self._field_mapping = {
                'text': 'text',
                'rating': 'rating',
                'author': 'author',
                'timestamp': 'timestamp',
                'source_id': 'id',
            }
        
        self._session = requests.Session()
        self._setup_auth()
    
    def _setup_auth(self):
        """Configure authentication for the session."""
        auth_type = self.config.auth_type.lower()
        
        if auth_type == 'api_key':
            header_name = self.config.auth_header or 'X-API-Key'
            self._session.headers[header_name] = self.config.api_key
            
        elif auth_type == 'bearer':
            self._session.headers['Authorization'] = f'Bearer {self.config.api_key}'
            
        elif auth_type == 'basic':
            self._session.auth = HTTPBasicAuth(
                self.config.api_key,
                self.config.api_secret or ''
            )
            
        elif auth_type == 'oauth':
            # OAuth would require additional setup
            self._session.headers['Authorization'] = f'OAuth {self.config.api_key}'
        
        # Add any custom headers
        self._session.headers.update(self._headers)
    
    def validate_config(self) -> List[str]:
        """Validate Generic API specific configuration."""
        errors = super().validate_config()
        
        if not self.config.api_endpoint:
            errors.append("api_endpoint is required for Generic API connector")
        
        if self.config.auth_type not in ['none', 'api_key', 'bearer', 'basic', 'oauth']:
            errors.append(f"Invalid auth_type: {self.config.auth_type}")
        
        if self.config.auth_type != 'none' and not self.config.api_key:
            errors.append("api_key is required when auth_type is not 'none'")
        
        return errors
    
    def test_connection(self) -> bool:
        """Test connection by making a simple request."""
        try:
            response = self._session.get(
                self.config.api_endpoint,
                params={'limit': 1, **self._params},
                timeout=self.config.timeout_seconds
            )
            return response.status_code in [200, 201]
        except Exception as e:
            self.last_error = str(e)
            return False
    
    def fetch_reviews(
        self,
        since: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> FetchResult:
        """
        Fetch reviews from the configured API endpoint.
        
        Args:
            since: Only fetch reviews after this datetime
            limit: Maximum number of reviews to fetch
        
        Returns:
            FetchResult with fetched reviews
        """
        limit = limit or self.config.fetch_limit
        self._log_fetch_start(since, limit)
        
        try:
            all_reviews = []
            offset = 0
            page = 1
            cursor = None
            
            while len(all_reviews) < limit:
                batch_limit = min(limit - len(all_reviews), 100)
                
                # Build request parameters
                params = {**self._params}
                
                # Add pagination parameters
                pagination_type = self._pagination.get('type', 'offset')
                
                if pagination_type == 'offset':
                    params[self._pagination.get('limit_param', 'limit')] = batch_limit
                    params[self._pagination.get('offset_param', 'offset')] = offset
                elif pagination_type == 'page':
                    params[self._pagination.get('limit_param', 'per_page')] = batch_limit
                    params[self._pagination.get('page_param', 'page')] = page
                elif pagination_type == 'cursor' and cursor:
                    params[self._pagination.get('cursor_param', 'cursor')] = cursor
                
                # Add date filter if supported
                if since and self._pagination.get('since_param'):
                    params[self._pagination['since_param']] = since.strftime(self._date_format)
                
                # Make request
                response = self._session.get(
                    self.config.api_endpoint,
                    params=params,
                    timeout=self.config.timeout_seconds
                )
                
                # Handle rate limiting
                if response.status_code == 429:
                    raise RateLimitError("API rate limit exceeded")
                
                # Handle authentication errors
                if response.status_code in [401, 403]:
                    raise AuthenticationError(f"Authentication failed: {response.status_code}")
                
                response.raise_for_status()
                
                # Parse response
                data = response.json()
                
                # Extract reviews from response path
                reviews_data = self._extract_reviews_from_response(data)
                
                if not reviews_data:
                    break
                
                # Convert to ReviewData objects
                for review_raw in reviews_data:
                    review = self._map_review(review_raw)
                    
                    if review and review.is_valid():
                        # Apply date filter
                        if since and review.timestamp and not self._is_after(review.timestamp, since):
                            continue
                        
                        # Apply rating filters
                        if self.config.min_rating and review.rating and review.rating < self.config.min_rating:
                            continue
                        if self.config.max_rating and review.rating and review.rating > self.config.max_rating:
                            continue
                        
                        all_reviews.append(review)
                
                # Update pagination state
                if pagination_type == 'offset':
                    offset += batch_limit
                elif pagination_type == 'page':
                    page += 1
                elif pagination_type == 'cursor':
                    cursor = self._extract_cursor(data)
                    if not cursor:
                        break
                
                # Check if we got fewer reviews than requested (end of data)
                if len(reviews_data) < batch_limit:
                    break
            
            result = FetchResult(
                reviews=all_reviews[:limit],
                success=True,
            )
            
            self._update_status_on_success(result)
            self._log_fetch_complete(result)
            return result
            
        except AuthenticationError as e:
            self._update_status_on_error(str(e))
            return FetchResult(
                reviews=[],
                success=False,
                error_message=str(e)
            )
        except RateLimitError as e:
            self.status = ConnectorStatus.RATE_LIMITED
            self.last_error = str(e)
            return FetchResult(
                reviews=[],
                success=False,
                error_message=str(e)
            )
        except requests.RequestException as e:
            self._update_status_on_error(str(e))
            return FetchResult(
                reviews=[],
                success=False,
                error_message=f"Request failed: {e}"
            )
        except Exception as e:
            self._update_status_on_error(str(e))
            return FetchResult(
                reviews=[],
                success=False,
                error_message=f"Fetch failed: {e}"
            )
    
    def _extract_reviews_from_response(self, data: Dict) -> List[Dict]:
        """Extract reviews array from API response using configured path."""
        if not self._response_path:
            # Assume root is the reviews array or has a common key
            if isinstance(data, list):
                return data
            for key in ['data', 'reviews', 'items', 'results']:
                if key in data:
                    value = data[key]
                    if isinstance(value, list):
                        return value
                    elif isinstance(value, dict) and 'reviews' in value:
                        return value['reviews']
            return []
        
        # Navigate the response path
        current = data
        for key in self._response_path.split('.'):
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return []
        
        return current if isinstance(current, list) else []
    
    def _extract_cursor(self, data: Dict) -> Optional[str]:
        """Extract pagination cursor from response."""
        cursor_path = self._pagination.get('cursor_response_path', 'next_cursor')
        
        current = data
        for key in cursor_path.split('.'):
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return str(current) if current else None
    
    def _map_review(self, raw: Dict) -> Optional[ReviewData]:
        """Map raw API response to ReviewData using field mapping."""
        try:
            # Extract fields using mapping
            text = self._get_nested_value(raw, self._field_mapping.get('text', 'text'))
            rating = self._get_nested_value(raw, self._field_mapping.get('rating', 'rating'))
            author = self._get_nested_value(raw, self._field_mapping.get('author', 'author'))
            timestamp_str = self._get_nested_value(raw, self._field_mapping.get('timestamp', 'timestamp'))
            source_id = self._get_nested_value(raw, self._field_mapping.get('source_id', 'id'))
            
            # Parse timestamp
            timestamp = None
            if timestamp_str:
                try:
                    if isinstance(timestamp_str, datetime):
                        timestamp = timestamp_str
                    elif isinstance(timestamp_str, (int, float)):
                        timestamp = datetime.fromtimestamp(timestamp_str)
                    else:
                        timestamp = datetime.strptime(str(timestamp_str), self._date_format)
                except:
                    try:
                        timestamp = datetime.fromisoformat(str(timestamp_str).replace('Z', '+00:00'))
                    except:
                        pass
            
            # Parse rating
            if rating is not None:
                try:
                    rating = float(rating)
                except:
                    rating = None
            
            return ReviewData(
                text=str(text) if text else "",
                rating=rating,
                author=str(author) if author else "Anonymous",
                timestamp=timestamp,
                source_id=str(source_id) if source_id else None,
                source=f"api:{self.config.name}",
                extra_data={k: v for k, v in raw.items() if k not in self._field_mapping.values()}
            )
            
        except Exception as e:
            self._logger.warning(f"Failed to map review: {e}")
            return None
    
    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Get a value from nested dictionary using dot notation."""
        if not path:
            return None
        
        current = data
        for key in path.split('.'):
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
