"""
Review Synchronization Service - Orchestrates automated review ingestion.

This service manages the complete workflow of:
1. Fetching reviews from multiple external sources via connectors
2. Converting and validating reviews
3. Deduplicating against existing data
4. Storing in the database
5. Triggering the NLP pipeline
6. Storing clustering results

The service acts as the central orchestrator connecting the Connector Layer
with the existing IngestionService and PipelineService.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Type
from dataclasses import dataclass, field
import json
import uuid

from review_clustering.connectors.base_connector import (
    BaseConnector,
    ConnectorConfig,
    ReviewData,
    FetchResult,
    ConnectorStatus,
)
from review_clustering.connectors.google_play_connector import GooglePlayConnector
from review_clustering.connectors.app_store_connector import AppStoreConnector
from review_clustering.connectors.generic_api_connector import GenericAPIConnector

# Lazy imports for services with heavy dependencies (embedding models, etc.)
# These are imported inside methods to avoid loading models at import time
# from review_clustering.services.ingestion_service import IngestionService
# from review_clustering.services.pipeline_service import PipelineService

logger = logging.getLogger(__name__)


@dataclass
class SyncJobResult:
    """
    Result of a synchronization job.
    
    Contains comprehensive information about what was fetched, processed,
    and any errors that occurred.
    """
    job_id: str
    connector_name: str
    source_type: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    
    # Fetch metrics
    reviews_fetched: int = 0
    reviews_valid: int = 0
    reviews_duplicate: int = 0
    reviews_stored: int = 0
    
    # Pipeline metrics
    pipeline_triggered: bool = False
    pipeline_run_id: Optional[str] = None
    clusters_created: int = 0
    
    # Status
    success: bool = True
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "job_id": self.job_id,
            "connector_name": self.connector_name,
            "source_type": self.source_type,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "reviews_fetched": self.reviews_fetched,
            "reviews_valid": self.reviews_valid,
            "reviews_duplicate": self.reviews_duplicate,
            "reviews_stored": self.reviews_stored,
            "pipeline_triggered": self.pipeline_triggered,
            "pipeline_run_id": self.pipeline_run_id,
            "clusters_created": self.clusters_created,
            "success": self.success,
            "error_message": self.error_message,
            "warnings": self.warnings,
            "duration_seconds": (
                (self.completed_at - self.started_at).total_seconds()
                if self.completed_at else None
            ),
        }


class ReviewSyncService:
    """
    Central orchestrator for automated review synchronization.
    
    Manages multiple connectors and coordinates the flow of reviews
    from external sources through the processing pipeline.
    
    Usage:
        # Initialize service
        sync_service = ReviewSyncService()
        
        # Register connectors
        sync_service.register_connector(GooglePlayConnector(config))
        sync_service.register_connector(AppStoreConnector(config))
        
        # Run synchronization
        results = sync_service.sync_all()
        
        # Or sync specific connector
        result = sync_service.sync_connector("my_app_google_play")
    """
    
    # Connector type registry
    CONNECTOR_TYPES: Dict[str, Type[BaseConnector]] = {
        "google_play": GooglePlayConnector,
        "app_store": AppStoreConnector,
        "api": GenericAPIConnector,
    }
    
    def __init__(self):
        """Initialize the synchronization service."""
        self._connectors: Dict[str, BaseConnector] = {}
        self._sync_history: List[SyncJobResult] = []
        self._last_sync_times: Dict[str, datetime] = {}
        self._is_running: bool = False
        self._logger = logging.getLogger(__name__)
    
    # =========================================================================
    # CONNECTOR MANAGEMENT
    # =========================================================================
    
    def register_connector(self, connector: BaseConnector) -> bool:
        """
        Register a connector for synchronization.
        
        Args:
            connector: Configured connector instance
        
        Returns:
            True if registration successful
        """
        # Validate configuration
        errors = connector.validate_config()
        if errors:
            self._logger.error(f"Invalid connector config: {errors}")
            return False
        
        self._connectors[connector.name] = connector
        self._logger.info(f"Registered connector: {connector.name} ({connector.source_type})")
        return True
    
    def register_connector_from_config(self, config: ConnectorConfig) -> bool:
        """
        Create and register a connector from configuration.
        
        Args:
            config: ConnectorConfig instance
        
        Returns:
            True if registration successful
        """
        connector_class = self.CONNECTOR_TYPES.get(config.source_type)
        if not connector_class:
            self._logger.error(f"Unknown connector type: {config.source_type}")
            return False
        
        connector = connector_class(config)
        return self.register_connector(connector)
    
    def unregister_connector(self, name: str) -> bool:
        """Remove a connector from the service."""
        if name in self._connectors:
            del self._connectors[name]
            self._logger.info(f"Unregistered connector: {name}")
            return True
        return False
    
    def get_connector(self, name: str) -> Optional[BaseConnector]:
        """Get a connector by name."""
        return self._connectors.get(name)
    
    def list_connectors(self) -> List[Dict[str, Any]]:
        """Get status of all registered connectors."""
        return [
            connector.get_status()
            for connector in self._connectors.values()
        ]
    
    # =========================================================================
    # SYNCHRONIZATION
    # =========================================================================
    
    def sync_all(
        self,
        trigger_pipeline: bool = True,
        force: bool = False
    ) -> List[SyncJobResult]:
        """
        Synchronize all enabled connectors.
        
        Args:
            trigger_pipeline: Whether to run NLP pipeline after ingestion
            force: Ignore fetch intervals and sync immediately
        
        Returns:
            List of SyncJobResult for each connector
        """
        if self._is_running:
            self._logger.warning("Sync already in progress")
            return []
        
        self._is_running = True
        results = []
        
        try:
            for name, connector in self._connectors.items():
                if not connector.is_enabled:
                    self._logger.info(f"Skipping disabled connector: {name}")
                    continue
                
                # Check if enough time has passed since last sync
                if not force:
                    last_sync = self._last_sync_times.get(name)
                    if last_sync:
                        interval = timedelta(minutes=connector.config.fetch_interval_minutes)
                        if datetime.utcnow() - last_sync < interval:
                            self._logger.info(f"Skipping {name}, synced recently")
                            continue
                
                result = self.sync_connector(
                    name,
                    trigger_pipeline=trigger_pipeline
                )
                results.append(result)
            
            return results
            
        finally:
            self._is_running = False
    
    def sync_connector(
        self,
        connector_name: str,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
        trigger_pipeline: bool = True
    ) -> SyncJobResult:
        """
        Synchronize a specific connector.
        
        Args:
            connector_name: Name of the connector to sync
            since: Only fetch reviews after this datetime
            limit: Maximum reviews to fetch
            trigger_pipeline: Whether to run NLP pipeline
        
        Returns:
            SyncJobResult with sync details
        """
        job_id = str(uuid.uuid4())
        started_at = datetime.utcnow()
        
        result = SyncJobResult(
            job_id=job_id,
            connector_name=connector_name,
            source_type="unknown",
            started_at=started_at,
        )
        
        try:
            # Get connector
            connector = self._connectors.get(connector_name)
            if not connector:
                result.success = False
                result.error_message = f"Connector not found: {connector_name}"
                return result
            
            result.source_type = connector.source_type
            
            # Determine since date (naive UTC)
            # Always use lookback_days so every sync fetches recent reviews.
            # Deduplication in _store_reviews handles repeated fetches.
            if not since:
                since = datetime.utcnow() - timedelta(
                    days=connector.config.lookback_days
                )
            # Strip timezone if present (normalize to naive UTC)
            if since.tzinfo is not None:
                since = since.astimezone(timezone.utc).replace(tzinfo=None)
            
            # Fetch reviews
            self._logger.info(f"Fetching reviews from {connector_name}")
            fetch_result = connector.fetch_reviews(since=since, limit=limit)
            
            if not fetch_result.success:
                result.success = False
                result.error_message = fetch_result.error_message
                return result
            
            result.reviews_fetched = fetch_result.count
            self._logger.info(f"Fetched {fetch_result.count} reviews")
            
            # Validate and filter reviews
            valid_reviews = [r for r in fetch_result.reviews if r.is_valid()]
            result.reviews_valid = len(valid_reviews)
            
            if result.reviews_fetched != result.reviews_valid:
                result.warnings.append(
                    f"{result.reviews_fetched - result.reviews_valid} invalid reviews filtered"
                )
            
            # Convert to ingestion format and store
            if valid_reviews:
                ingestion_result = self._store_reviews(valid_reviews, connector.source_type)
                result.reviews_stored = ingestion_result.get('successful', 0)
                result.reviews_duplicate = ingestion_result.get('duplicates', 0)
                
                if ingestion_result.get('failed', 0) > 0:
                    result.warnings.append(
                        f"{ingestion_result['failed']} reviews failed to store"
                    )
            
            # Trigger pipeline if requested and we have new reviews
            if trigger_pipeline and result.reviews_stored > 0:
                pipeline_result = self._trigger_pipeline()
                result.pipeline_triggered = True
                result.pipeline_run_id = pipeline_result.get('run_id')
                result.clusters_created = pipeline_result.get('num_clusters', 0)
            
            # Update last sync time
            self._last_sync_times[connector_name] = started_at
            
        except Exception as e:
            result.success = False
            result.error_message = str(e)
            self._logger.error(f"Sync failed for {connector_name}: {e}")
        
        finally:
            result.completed_at = datetime.utcnow()
            self._sync_history.append(result)
        
        return result
    
    def _store_reviews(
        self,
        reviews: List[ReviewData],
        source_type: str
    ) -> Dict[str, Any]:
        """
        Store reviews using the IngestionService.
        
        Converts ReviewData objects to the format expected by IngestionService.
        """
        # Lazy import to avoid loading heavy dependencies at module import time
        from review_clustering.services.ingestion_service import IngestionService
        
        # Convert to ingestion format
        api_reviews = []
        for review in reviews:
            api_reviews.append({
                'text': review.text,
                'rating': review.rating,
                'author': review.author,
                'timestamp': review.timestamp.isoformat() if review.timestamp else None,
                'source_id': review.source_id,
                'metadata': json.dumps(review.extra_data) if review.extra_data else None,
            })
        
        # Use existing IngestionService
        try:
            result = IngestionService.ingest_api(api_reviews, source=source_type)
            return result
        except Exception as e:
            self._logger.error(f"Failed to store reviews: {e}")
            return {
                'successful': 0,
                'failed': len(reviews),
                'duplicates': 0,
                'error': str(e)
            }
    
    def _trigger_pipeline(self) -> Dict[str, Any]:
        """
        Trigger the NLP processing pipeline.
        
        Fetches pending reviews and runs them through the clustering pipeline.
        """
        # Lazy imports to avoid loading heavy dependencies at module import time
        from review_clustering.services.ingestion_service import IngestionService
        from review_clustering.services.pipeline_service import PipelineService
        
        try:
            # Get pending reviews from database
            pending_reviews = IngestionService.get_pending_reviews(limit=1000)

            # No raw reviews waiting to be processed
            if not pending_reviews:
                return {
                    'run_id': None,
                    'num_clusters': 0,
                    'message': 'No pending reviews'
                }

            # Convert RawReview dicts to the format expected by PipelineService
            items: List[Dict[str, Any]] = []
            review_ids: List[int] = []
            for review in pending_reviews:
                text = review.get('text') or review.get('review_text') or ''
                if not text:
                    continue

                items.append({
                    'text': text,
                    'timestamp': review.get('timestamp')
                })

                if review.get('id') is not None:
                    review_ids.append(review['id'])

            # If nothing valid after mapping, don't call the heavy pipeline
            if not items:
                return {
                    'run_id': None,
                    'num_clusters': 0,
                    'message': 'No valid reviews to process'
                }

            # Run pipeline
            result = PipelineService.run_pipeline(
                raw_items=items,
                save_to_db=True
            )

            # If the pipeline reported an error, surface it and avoid
            # marking the reviews as processed so they can be retried.
            if result.get('error'):
                return {
                    'run_id': None,
                    'num_clusters': 0,
                    'message': result.get('error')
                }

            # Mark these reviews as processed so they are not reprocessed
            if review_ids:
                IngestionService.mark_as_processed(review_ids)

            return {
                'run_id': result.get('run_id'),
                'num_clusters': len(result.get('cluster_summary', {})),
                'trend_score': result.get('trend_score'),
            }
            
        except Exception as e:
            self._logger.error(f"Pipeline failed: {e}")
            return {'error': str(e)}
    
    # =========================================================================
    # HISTORY AND REPORTING
    # =========================================================================
    
    def get_sync_history(
        self,
        connector_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get history of sync jobs.
        
        Args:
            connector_name: Filter by connector name
            limit: Maximum number of results
        
        Returns:
            List of sync job results
        """
        history = self._sync_history
        
        if connector_name:
            history = [h for h in history if h.connector_name == connector_name]
        
        # Sort by started_at descending
        history = sorted(history, key=lambda x: x.started_at, reverse=True)
        
        return [h.to_dict() for h in history[:limit]]
    
    def get_sync_stats(self) -> Dict[str, Any]:
        """
        Get aggregate synchronization statistics.
        
        Returns:
            Dictionary with overall sync metrics
        """
        if not self._sync_history:
            return {
                'total_syncs': 0,
                'successful_syncs': 0,
                'failed_syncs': 0,
                'total_reviews_fetched': 0,
                'total_reviews_stored': 0,
                'total_duplicates': 0,
                'connectors_count': len(self._connectors),
            }
        
        return {
            'total_syncs': len(self._sync_history),
            'successful_syncs': sum(1 for h in self._sync_history if h.success),
            'failed_syncs': sum(1 for h in self._sync_history if not h.success),
            'total_reviews_fetched': sum(h.reviews_fetched for h in self._sync_history),
            'total_reviews_stored': sum(h.reviews_stored for h in self._sync_history),
            'total_duplicates': sum(h.reviews_duplicate for h in self._sync_history),
            'total_clusters_created': sum(h.clusters_created for h in self._sync_history),
            'connectors_count': len(self._connectors),
            'last_sync': max(h.started_at for h in self._sync_history).isoformat(),
        }
    
    def is_running(self) -> bool:
        """Check if sync is currently running."""
        return self._is_running


# Global singleton instance
_sync_service_instance: Optional[ReviewSyncService] = None


def get_sync_service() -> ReviewSyncService:
    """Get the global ReviewSyncService instance."""
    global _sync_service_instance
    if _sync_service_instance is None:
        _sync_service_instance = ReviewSyncService()
    return _sync_service_instance
