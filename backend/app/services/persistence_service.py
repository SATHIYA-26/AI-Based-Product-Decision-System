"""Service for persisting pipeline results to database."""

import uuid
from typing import Dict, List
from datetime import datetime

from app.models.cluster_analysis import ClusterResult, PipelineRun, get_db_session


class PersistenceService:
    """Handles all database write operations for pipeline results."""
    
    @staticmethod
    def save_pipeline_run(
        num_inputs: int,
        num_cleaned: int,
        cluster_summary: Dict,
        execution_time_ms: int = None,
        status: str = "completed",
        error_message: str = ""
    ) -> str:
        """Save a full pipeline execution and all its cluster results.
        
        Returns:
            run_id: A unique identifier for this pipeline run (for later lookup)
        """
        session = get_db_session()
        
        try:
            run_id = str(uuid.uuid4())
            
            # record the run metadata
            num_clusters = len(cluster_summary)
            pipeline_run = PipelineRun(
                run_id=run_id,
                num_inputs=num_inputs,
                num_cleaned=num_cleaned,
                num_clusters=num_clusters,
                status=status,
                error_message=error_message,
                execution_time_ms=execution_time_ms
            )
            session.add(pipeline_run)
            session.commit()
            
            # save each cluster result
            for cluster_id, cluster_data in cluster_summary.items():
                result = ClusterResult(
                    run_id=run_id,
                    cluster_id=cluster_id,
                    frequency=cluster_data["frequency"],
                    avg_sentiment=cluster_data["avg_sentiment"],
                    priority_score=cluster_data["priority_score"],
                    trend_score=cluster_data.get("trend_score", 0.0),
                    summary=cluster_data.get("summary", ""),
                    label=cluster_data.get("label", ""),
                    representative_reviews=cluster_data.get("representative_reviews", [])
                )
                session.add(result)
            
            session.commit()
            return run_id
            
        except Exception as e:
            session.rollback()
            print(f"[PersistenceService] Error saving run: {e}")
            raise
        finally:
            session.close()
    
    @staticmethod
    def get_run_by_id(run_id: str) -> Dict:
        """Fetch a full pipeline run and all its clusters by run_id.
        
        Returns:
            dict with keys:
                - run: PipelineRun metadata
                - clusters: List of ClusterResult dicts
        """
        session = get_db_session()
        
        try:
            run = session.query(PipelineRun).filter_by(run_id=run_id).first()
            if not run:
                return None
            
            clusters = session.query(ClusterResult).filter_by(run_id=run_id).all()
            
            return {
                "run": run.to_dict(),
                "clusters": [c.to_dict() for c in clusters]
            }
        finally:
            session.close()
    
    @staticmethod
    def list_recent_runs(limit: int = 10) -> List[Dict]:
        """List the most recent pipeline runs.
        
        Returns:
            List of PipelineRun dicts, ordered by creation date (newest first)
        """
        session = get_db_session()
        
        try:
            runs = session.query(PipelineRun)\
                .order_by(PipelineRun.created_at.desc())\
                .limit(limit)\
                .all()
            return [r.to_dict() for r in runs]
        finally:
            session.close()
    
    @staticmethod
    def get_clusters_by_priority(limit: int = 10) -> List[Dict]:
        """Get the highest priority clusters across all recent runs.
        
        Returns:
            List of ClusterResult dicts sorted by priority_score (descending)
        """
        session = get_db_session()
        
        try:
            clusters = session.query(ClusterResult)\
                .order_by(ClusterResult.priority_score.desc())\
                .limit(limit)\
                .all()
            return [c.to_dict() for c in clusters]
        finally:
            session.close()
