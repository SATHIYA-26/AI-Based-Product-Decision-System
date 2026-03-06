"""Service for ingesting reviews from various sources."""

import csv
import io
from typing import List, Dict, Tuple
from datetime import datetime

from review_clustering.models.ingestion import RawReview, IngestionJob, get_ingestion_db_session


class IngestionService:
    """Handles data ingestion from CSV, API, and scheduled sources."""
    
    @staticmethod
    def _create_ingestion_job(job_type: str, source: str) -> IngestionJob:
        """Create a new ingestion job record."""
        session = get_ingestion_db_session()
        try:
            job = IngestionJob(job_type=job_type, source=source, status="running")
            session.add(job)
            session.commit()
            job_id = job.id
            session.close()
            return job_id
        except Exception as e:
            session.rollback()
            session.close()
            raise Exception(f"Failed to create ingestion job: {e}")
    
    @staticmethod
    def _update_ingestion_job(job_id: int, status: str, successful: int, failed: int, 
                              duplicates: int, total: int, error_msg: str = ""):
        """Update job status and results."""
        session = get_ingestion_db_session()
        try:
            job = session.query(IngestionJob).filter_by(id=job_id).first()
            if job:
                job.status = status
                job.successful = successful
                job.failed = failed
                job.duplicates_found = duplicates
                job.total_records = total
                job.error_message = error_msg
                if status == "completed" or status == "failed":
                    job.completed_at = datetime.utcnow()
                session.commit()
        finally:
            session.close()
    
    @staticmethod
    def ingest_csv(csv_file_content: str, source: str = "csv_upload") -> Dict:
        """Ingest reviews from a CSV file.
        
        Expected columns: review_text (required), rating, author, timestamp
        
        Args:
            csv_file_content: Raw CSV text
            source: Label for this ingestion source (default: csv_upload)
            
        Returns:
            Dict with ingestion stats
        """
        job_id = IngestionService._create_ingestion_job("csv_upload", source)
        session = get_ingestion_db_session()
        
        try:
            # Parse CSV
            csv_reader = csv.DictReader(io.StringIO(csv_file_content))
            if not csv_reader.fieldnames or "review_text" not in csv_reader.fieldnames:
                raise ValueError("CSV must contain 'review_text' column")
            
            rows = list(csv_reader)
            total = len(rows)
            successful = 0
            failed = 0
            duplicates = 0
            
            # Get existing reviews to check for duplicates
            existing_texts = set()
            for review in session.query(RawReview).all():
                existing_texts.add(review.review_text.lower().strip())
            
            for row in rows:
                try:
                    text = row.get("review_text", "").strip()
                    if not text:
                        failed += 1
                        continue
                    
                    # Check for duplicates
                    if text.lower() in existing_texts:
                        duplicates += 1
                        continue
                    
                    existing_texts.add(text.lower())
                    
                    # Parse optional fields
                    rating = None
                    try:
                        rating = float(row.get("rating", 0))
                    except (ValueError, TypeError):
                        pass
                    
                    timestamp = None
                    try:
                        ts_str = row.get("timestamp", "")
                        if ts_str:
                            timestamp = datetime.fromisoformat(ts_str)
                    except (ValueError, TypeError):
                        pass
                    
                    review = RawReview(
                        source=source,
                        source_id=row.get("source_id"),
                        review_text=text,
                        rating=rating,
                        author=row.get("author"),
                        timestamp=timestamp
                    )
                    session.add(review)
                    successful += 1
                    
                except Exception as e:
                    failed += 1
                    continue
            
            session.commit()
            
            IngestionService._update_ingestion_job(
                job_id, "completed", successful, failed, duplicates, total
            )
            
            return {
                "job_id": job_id,
                "source": source,
                "total": total,
                "successful": successful,
                "failed": failed,
                "duplicates": duplicates,
                "status": "completed"
            }
            
        except Exception as e:
            IngestionService._update_ingestion_job(job_id, "failed", 0, total, 0, total, str(e))
            return {"job_id": job_id, "status": "failed", "error": str(e)}
        finally:
            session.close()
    
    @staticmethod
    def ingest_api(reviews: List[Dict], source: str = "api") -> Dict:
        """Ingest reviews from API payload.
        
        Expected fields in each review dict:
            - text (required)
            - rating (optional)
            - author (optional)
            - timestamp (optional)
            - source_id (optional)
        
        Args:
            reviews: List of review dicts
            source: Label for this ingestion source
            
        Returns:
            Dict with ingestion stats
        """
        job_id = IngestionService._create_ingestion_job("api_import", source)
        session = get_ingestion_db_session()
        
        try:
            total = len(reviews)
            successful = 0
            failed = 0
            duplicates = 0
            
            # Get existing reviews
            existing_texts = set()
            for review in session.query(RawReview).all():
                existing_texts.add(review.review_text.lower().strip())
            
            for review_data in reviews:
                try:
                    text = review_data.get("text", "").strip()
                    if not text:
                        failed += 1
                        continue
                    
                    if text.lower() in existing_texts:
                        duplicates += 1
                        continue
                    
                    existing_texts.add(text.lower())
                    
                    # Parse optional fields
                    rating = None
                    try:
                        rating = float(review_data.get("rating", 0))
                    except (ValueError, TypeError):
                        pass
                    
                    timestamp = None
                    try:
                        ts_str = review_data.get("timestamp", "")
                        if ts_str:
                            if isinstance(ts_str, str):
                                timestamp = datetime.fromisoformat(ts_str)
                            else:
                                timestamp = ts_str
                    except (ValueError, TypeError, AttributeError):
                        pass
                    
                    raw_review = RawReview(
                        source=source,
                        source_id=review_data.get("source_id"),
                        review_text=text,
                        rating=rating,
                        author=review_data.get("author"),
                        timestamp=timestamp
                    )
                    session.add(raw_review)
                    successful += 1
                    
                except Exception as e:
                    failed += 1
                    continue
            
            session.commit()
            
            IngestionService._update_ingestion_job(
                job_id, "completed", successful, failed, duplicates, total
            )
            
            return {
                "job_id": job_id,
                "source": source,
                "total": total,
                "successful": successful,
                "failed": failed,
                "duplicates": duplicates,
                "status": "completed"
            }
            
        except Exception as e:
            IngestionService._update_ingestion_job(job_id, "failed", 0, total, 0, total, str(e))
            return {"job_id": job_id, "status": "failed", "error": str(e)}
        finally:
            session.close()
    
    @staticmethod
    def get_pending_reviews(limit: int = 1000) -> List[Dict]:
        """Fetch reviews that haven't been processed yet."""
        session = get_ingestion_db_session()
        try:
            reviews = session.query(RawReview)\
                .filter_by(is_duplicate=False)\
                .limit(limit)\
                .all()
            return [r.to_dict() for r in reviews]
        finally:
            session.close()
    
    @staticmethod
    def mark_as_processed(review_ids: List[int]):
        """Mark reviews as processed (so they're not reprocessed)."""
        session = get_ingestion_db_session()
        try:
            session.query(RawReview)\
                .filter(RawReview.id.in_(review_ids))\
                .update({"is_duplicate": True}, synchronize_session='fetch')
            session.commit()
        finally:
            session.close()
    
    @staticmethod
    def get_ingestion_jobs(limit: int = 20) -> List[Dict]:
        """Get recent ingestion job history."""
        session = get_ingestion_db_session()
        try:
            jobs = session.query(IngestionJob)\
                .order_by(IngestionJob.started_at.desc())\
                .limit(limit)\
                .all()
            return [j.to_dict() for j in jobs]
        finally:
            session.close()
