"""
Automated Scheduler Service - Manages periodic review synchronization.

This service uses APScheduler to automatically fetch reviews from configured
connectors at specified intervals. It handles:
- Scheduled sync jobs
- Retry logic for failed syncs
- Concurrent execution limits
- Job status tracking
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any, Callable
from threading import Lock
import atexit

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED

from review_clustering.services.sync_service import (
    ReviewSyncService,
    get_sync_service,
    SyncJobResult,
)
from review_clustering.models.sync_models import (
    save_sync_job,
    get_sync_jobs,
    get_connector_configs,
    SyncSchedule,
    get_sync_db_session,
)

logger = logging.getLogger(__name__)


class AutomatedSchedulerService:
    """
    Manages automated scheduling of review synchronization.
    
    Features:
    - Interval-based scheduling (every N minutes)
    - Cron-based scheduling (specific times)
    - Execution windows (only run during certain hours)
    - Automatic retry on failure
    - Concurrent job limiting
    - Job monitoring and status tracking
    
    Usage:
        scheduler = AutomatedSchedulerService()
        
        # Add a connector with interval scheduling
        scheduler.add_sync_job(
            connector_name="my_app_google_play",
            interval_minutes=60
        )
        
        # Add a connector with cron scheduling
        scheduler.add_sync_job(
            connector_name="my_app_app_store",
            cron_expression="0 */2 * * *"  # Every 2 hours
        )
        
        # Start the scheduler
        scheduler.start()
    """
    
    def __init__(
        self,
        sync_service: Optional[ReviewSyncService] = None,
        max_concurrent_jobs: int = 3
    ):
        """
        Initialize the scheduler service.
        
        Args:
            sync_service: ReviewSyncService instance (uses global if not provided)
            max_concurrent_jobs: Maximum number of concurrent sync jobs
        """
        self._sync_service = sync_service or get_sync_service()
        self._max_concurrent_jobs = max_concurrent_jobs
        
        # Initialize APScheduler
        self._scheduler = BackgroundScheduler(
            job_defaults={
                'coalesce': True,  # Combine missed runs into one
                'max_instances': 1,  # Only one instance per job at a time
                'misfire_grace_time': 300,  # 5 minutes grace period
            }
        )
        
        # Track running jobs
        self._running_jobs: Dict[str, datetime] = {}
        self._job_lock = Lock()
        
        # Statistics
        self._stats = {
            'total_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'last_run': None,
        }
        
        # Register event listeners
        self._scheduler.add_listener(
            self._on_job_executed,
            EVENT_JOB_EXECUTED
        )
        self._scheduler.add_listener(
            self._on_job_error,
            EVENT_JOB_ERROR
        )
        self._scheduler.add_listener(
            self._on_job_missed,
            EVENT_JOB_MISSED
        )
        
        # Ensure scheduler is shut down on exit
        atexit.register(self.shutdown)
        
        self._logger = logging.getLogger(__name__)
    
    # =========================================================================
    # SCHEDULER LIFECYCLE
    # =========================================================================
    
    def start(self):
        """Start the scheduler."""
        if not self._scheduler.running:
            self._scheduler.start()
            self._logger.info("Automated scheduler started")
    
    def shutdown(self, wait: bool = True):
        """
        Shut down the scheduler.
        
        Args:
            wait: Wait for running jobs to complete
        """
        if self._scheduler.running:
            self._scheduler.shutdown(wait=wait)
            self._logger.info("Automated scheduler stopped")
    
    def pause(self):
        """Pause the scheduler (jobs won't run but scheduler stays active)."""
        self._scheduler.pause()
        self._logger.info("Automated scheduler paused")
    
    def resume(self):
        """Resume a paused scheduler."""
        self._scheduler.resume()
        self._logger.info("Automated scheduler resumed")
    
    @property
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._scheduler.running
    
    # =========================================================================
    # JOB MANAGEMENT
    # =========================================================================
    
    def add_sync_job(
        self,
        connector_name: str,
        interval_minutes: Optional[int] = None,
        cron_expression: Optional[str] = None,
        start_hour: Optional[int] = None,
        end_hour: Optional[int] = None,
        trigger_pipeline: bool = True,
        replace_existing: bool = True
    ) -> str:
        """
        Add a scheduled sync job for a connector.
        
        Args:
            connector_name: Name of the connector to sync
            interval_minutes: Run every N minutes
            cron_expression: Cron expression for scheduling
            start_hour: Only run after this hour (0-23)
            end_hour: Only run before this hour (0-23)
            trigger_pipeline: Whether to run NLP pipeline after sync
            replace_existing: Replace existing job with same name
        
        Returns:
            Job ID
        
        Raises:
            ValueError: If neither interval nor cron is specified
        """
        if not interval_minutes and not cron_expression:
            raise ValueError("Must specify either interval_minutes or cron_expression")
        
        job_id = f"sync_{connector_name}"
        
        # Create trigger
        if cron_expression:
            trigger = CronTrigger.from_crontab(cron_expression)
        else:
            trigger = IntervalTrigger(minutes=interval_minutes)
        
        # Wrap the sync function with execution window check
        def job_func():
            # Check execution window
            if start_hour is not None or end_hour is not None:
                current_hour = datetime.now().hour
                if start_hour is not None and current_hour < start_hour:
                    self._logger.debug(f"Skipping {connector_name}: before execution window")
                    return
                if end_hour is not None and current_hour >= end_hour:
                    self._logger.debug(f"Skipping {connector_name}: after execution window")
                    return
            
            # Check concurrent job limit
            with self._job_lock:
                if len(self._running_jobs) >= self._max_concurrent_jobs:
                    self._logger.warning(f"Skipping {connector_name}: max concurrent jobs reached")
                    return
                self._running_jobs[connector_name] = datetime.utcnow()
            
            try:
                self._execute_sync(connector_name, trigger_pipeline)
            finally:
                with self._job_lock:
                    self._running_jobs.pop(connector_name, None)
        
        # Add job to scheduler
        self._scheduler.add_job(
            job_func,
            trigger=trigger,
            id=job_id,
            name=f"Sync: {connector_name}",
            replace_existing=replace_existing,
        )
        
        self._logger.info(
            f"Added sync job: {connector_name}, "
            f"interval={interval_minutes}min, cron={cron_expression}"
        )
        
        return job_id
    
    def remove_sync_job(self, connector_name: str) -> bool:
        """
        Remove a scheduled sync job.
        
        Args:
            connector_name: Name of the connector
        
        Returns:
            True if job was removed
        """
        job_id = f"sync_{connector_name}"
        
        try:
            self._scheduler.remove_job(job_id)
            self._logger.info(f"Removed sync job: {connector_name}")
            return True
        except Exception as e:
            self._logger.warning(f"Failed to remove job {connector_name}: {e}")
            return False
    
    def pause_sync_job(self, connector_name: str) -> bool:
        """Pause a specific sync job."""
        job_id = f"sync_{connector_name}"
        
        try:
            self._scheduler.pause_job(job_id)
            return True
        except Exception:
            return False
    
    def resume_sync_job(self, connector_name: str) -> bool:
        """Resume a paused sync job."""
        job_id = f"sync_{connector_name}"
        
        try:
            self._scheduler.resume_job(job_id)
            return True
        except Exception:
            return False
    
    def trigger_sync_now(
        self,
        connector_name: str,
        trigger_pipeline: bool = True
    ) -> Optional[SyncJobResult]:
        """
        Trigger an immediate sync for a connector.
        
        Args:
            connector_name: Name of the connector
            trigger_pipeline: Whether to run NLP pipeline
        
        Returns:
            SyncJobResult if executed, None if skipped
        """
        # Check if already running
        with self._job_lock:
            if connector_name in self._running_jobs:
                self._logger.warning(f"Sync already running for {connector_name}")
                return None
            self._running_jobs[connector_name] = datetime.utcnow()
        
        try:
            return self._execute_sync(connector_name, trigger_pipeline)
        finally:
            with self._job_lock:
                self._running_jobs.pop(connector_name, None)
    
    def _execute_sync(
        self,
        connector_name: str,
        trigger_pipeline: bool
    ) -> SyncJobResult:
        """Execute a sync operation for a connector."""
        self._logger.info(f"Executing sync for: {connector_name}")
        
        try:
            result = self._sync_service.sync_connector(
                connector_name,
                trigger_pipeline=trigger_pipeline
            )
            
            # Save result to database
            try:
                save_sync_job(result)
            except Exception as e:
                self._logger.warning(f"Failed to save sync job to DB: {e}")
            
            # Update statistics
            self._stats['total_runs'] += 1
            self._stats['last_run'] = datetime.utcnow()
            if result.success:
                self._stats['successful_runs'] += 1
            else:
                self._stats['failed_runs'] += 1
            
            return result
            
        except Exception as e:
            self._logger.error(f"Sync execution failed: {e}")
            raise
    
    # =========================================================================
    # STATUS AND MONITORING
    # =========================================================================
    
    def get_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """Get list of all scheduled jobs with their status."""
        jobs = []
        
        for job in self._scheduler.get_jobs():
            # Handle different APScheduler versions
            try:
                next_run = getattr(job, 'next_run_time', None)
            except Exception:
                next_run = None
            
            jobs.append({
                'job_id': job.id,
                'name': job.name,
                'next_run': next_run.isoformat() if next_run else None,
                'paused': next_run is None,
                'trigger': str(job.trigger),
            })
        
        return jobs
    
    def get_running_jobs(self) -> Dict[str, str]:
        """Get currently running sync jobs."""
        with self._job_lock:
            return {
                name: started.isoformat()
                for name, started in self._running_jobs.items()
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status and statistics."""
        return {
            'running': self.is_running,
            'scheduled_jobs': len(self._scheduler.get_jobs()),
            'running_jobs': len(self._running_jobs),
            'max_concurrent_jobs': self._max_concurrent_jobs,
            'statistics': {
                **self._stats,
                'last_run': self._stats['last_run'].isoformat() if self._stats['last_run'] else None,
            },
        }
    
    # =========================================================================
    # EVENT HANDLERS
    # =========================================================================
    
    def _on_job_executed(self, event):
        """Handle successful job execution."""
        self._logger.debug(f"Job executed: {event.job_id}")
    
    def _on_job_error(self, event):
        """Handle job execution error."""
        self._logger.error(f"Job error: {event.job_id}, exception: {event.exception}")
    
    def _on_job_missed(self, event):
        """Handle missed job execution."""
        self._logger.warning(f"Job missed: {event.job_id}")
    
    # =========================================================================
    # CONFIGURATION LOADING
    # =========================================================================
    
    def load_from_database(self):
        """
        Load connector configurations and schedules from database.
        
        Registers connectors with the sync service and adds scheduled jobs.
        """
        try:
            # Load connector configurations
            configs = get_connector_configs(enabled_only=True)
            
            for config_dict in configs:
                # Register connector
                from review_clustering.connectors.base_connector import ConnectorConfig
                
                config = ConnectorConfig(
                    name=config_dict['name'],
                    source_type=config_dict['connector_type'],
                    enabled=config_dict['enabled'],
                    api_endpoint=config_dict.get('api_endpoint'),
                    api_key=config_dict.get('api_key_encrypted'),
                    app_id=config_dict.get('app_id'),
                    product_id=config_dict.get('product_id'),
                    fetch_limit=config_dict.get('fetch_limit', 100),
                    fetch_interval_minutes=config_dict.get('fetch_interval_minutes', 60),
                    lookback_days=config_dict.get('lookback_days', 7),
                    min_rating=config_dict.get('min_rating'),
                    max_rating=config_dict.get('max_rating'),
                    languages=config_dict.get('languages', []),
                    extra_config=config_dict.get('extra_config', {}),
                )
                
                self._sync_service.register_connector_from_config(config)
                
                # Add scheduled job
                self.add_sync_job(
                    config.name,
                    interval_minutes=config.fetch_interval_minutes,
                )
            
            self._logger.info(f"Loaded {len(configs)} connector configurations")
            
        except Exception as e:
            self._logger.error(f"Failed to load from database: {e}")
            raise


# Global singleton instance
_scheduler_instance: Optional[AutomatedSchedulerService] = None


def get_scheduler_service() -> AutomatedSchedulerService:
    """Get the global AutomatedSchedulerService instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = AutomatedSchedulerService()
    return _scheduler_instance


def start_automated_sync(
    connectors: List[Dict[str, Any]] = None,
    default_interval_minutes: int = 60
) -> AutomatedSchedulerService:
    """
    Convenience function to start automated synchronization.
    
    Args:
        connectors: List of connector configurations
        default_interval_minutes: Default sync interval
    
    Returns:
        AutomatedSchedulerService instance
    
    Example:
        start_automated_sync([
            {
                'name': 'my_app_google_play',
                'source_type': 'google_play',
                'app_id': 'com.example.myapp',
                'interval_minutes': 30,
            },
            {
                'name': 'my_app_app_store',
                'source_type': 'app_store',
                'app_id': '123456789',
                'interval_minutes': 60,
            },
        ])
    """
    scheduler = get_scheduler_service()
    sync_service = get_sync_service()
    
    if connectors:
        from review_clustering.connectors.base_connector import ConnectorConfig
        
        for conn_config in connectors:
            config = ConnectorConfig(
                name=conn_config['name'],
                source_type=conn_config['source_type'],
                app_id=conn_config.get('app_id'),
                api_endpoint=conn_config.get('api_endpoint'),
                api_key=conn_config.get('api_key'),
                fetch_limit=conn_config.get('fetch_limit', 100),
                fetch_interval_minutes=conn_config.get('interval_minutes', default_interval_minutes),
                lookback_days=conn_config.get('lookback_days', 7),
                min_rating=conn_config.get('min_rating'),
                max_rating=conn_config.get('max_rating'),
                languages=conn_config.get('languages', []),
                extra_config=conn_config.get('extra_config', {}),
            )
            
            sync_service.register_connector_from_config(config)
            
            scheduler.add_sync_job(
                config.name,
                interval_minutes=config.fetch_interval_minutes,
            )
    
    scheduler.start()
    return scheduler
