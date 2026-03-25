"""Flask application with REST endpoints for ingestion and clustering."""

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from apscheduler.schedulers.background import BackgroundScheduler
import os
import json

from review_clustering.services.ingestion_service import IngestionService
from review_clustering.services.pipeline_service import PipelineService
from review_clustering.services.sync_service import get_sync_service, ReviewSyncService
from review_clustering.services.scheduler_service import (
    get_scheduler_service, AutomatedSchedulerService, start_automated_sync
)
from review_clustering.connectors import (
    ConnectorConfig, ReviewData, GooglePlayConnector, AppStoreConnector, GenericAPIConnector
)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), '..', 'uploads')

# Enable CORS for all routes
CORS(app, origins=['http://localhost:3000', 'http://127.0.0.1:3000'])

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], mode=0o755, exist_ok=True)

scheduler = BackgroundScheduler()
scheduler_started = False


# ============================================================================
# DATA INGESTION ENDPOINTS
# ============================================================================

@app.route('/upload-csv', methods=['POST'])
def upload_csv():
    """Upload reviews from a CSV file.
    
    Expected format:
    review_text,rating,author,timestamp
    Login not working,1,john,2026-02-27T10:00:00
    Payment failed,2,jane,2026-02-27T11:00:00
    
    Returns:
        JSON with ingestion results
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({"error": "File must be CSV"}), 400
    
    try:
        csv_content = file.read().decode('utf-8')
        source = request.form.get('source', 'csv_upload')
        
        result = IngestionService.ingest_csv(csv_content, source)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500


@app.route('/ingest-api', methods=['POST'])
def ingest_api():
    """Ingest reviews from JSON API payload.
    
    Expected JSON:
    {
        "reviews": [
            {"text": "Login not working", "rating": 1, "author": "john", "timestamp": "2026-02-27T10:00:00"},
            {"text": "Payment failed", "rating": 2, "author": "jane"}
        ],
        "source": "app_store"
    }
    
    Returns:
        JSON with ingestion results
    """
    try:
        data = request.get_json()
        if not data or 'reviews' not in data:
            return jsonify({"error": "Request must include 'reviews' field"}), 400
        
        reviews = data.get('reviews', [])
        source = data.get('source', 'api')
        
        if not isinstance(reviews, list) or len(reviews) == 0:
            return jsonify({"error": "reviews must be a non-empty list"}), 400
        
        result = IngestionService.ingest_api(reviews, source)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": f"API ingestion failed: {str(e)}"}), 500


@app.route('/ingestion-status', methods=['GET'])
def ingestion_status():
    """Get status of recent ingestion jobs."""
    try:
        limit = request.args.get('limit', 10, type=int)
        jobs = IngestionService.get_ingestion_jobs(limit)
        return jsonify({"jobs": jobs}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# CLUSTERING / PIPELINE ENDPOINTS
# ============================================================================

@app.route('/process-reviews', methods=['POST'])
def process_reviews():
    """Process pending reviews through the clustering pipeline.
    
    Fetches all unprocessed reviews from the database and runs them through
    the full pipeline (filtering, clustering, sentiment, priority, etc.)
    
    Returns:
        JSON with clustering results and saved run_id
    """
    try:
        limit = request.args.get('limit', 1000, type=int)
        
        # Get pending reviews from database
        pending = IngestionService.get_pending_reviews(limit)
        if not pending:
            return jsonify({"message": "No pending reviews to process"}), 200
        
        # Convert to format expected by pipeline (text and timestamp)
        items = []
        review_ids = []
        for review in pending:
            items.append({
                "text": review["review_text"],
                "timestamp": review["timestamp"]
            })
            review_ids.append(review["id"])
        
        # Run clustering pipeline
        result = PipelineService.run_pipeline(items, save_to_db=True)
        
        # Mark these reviews as processed
        IngestionService.mark_as_processed(review_ids)
        
        return jsonify({
            "status": "success",
            "reviews_processed": len(review_ids),
            "run_id": result.get("run_id"),
            "clusters": len(result.get("cluster_summary", {})),
            "execution_time_ms": result.get("execution_time_ms")
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500


@app.route('/cluster-results/<run_id>', methods=['GET'])
def get_cluster_results(run_id):
    """Get clustering results for a specific pipeline run.
    
    Args:
        run_id: UUID of the pipeline run
        
    Returns:
        JSON with cluster summary and metadata
    """
    try:
        from review_clustering.services.persistence_service import PersistenceService
        
        result = PersistenceService.get_run_by_id(run_id)
        if not result:
            return jsonify({"error": "Run not found"}), 404
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/top-clusters', methods=['GET'])
def get_top_clusters():
    """Get highest priority clusters across all runs."""
    try:
        from review_clustering.services.persistence_service import PersistenceService
        
        limit = request.args.get('limit', 10, type=int)
        clusters = PersistenceService.get_clusters_by_priority(limit)
        return jsonify({"clusters": clusters}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/customer-problems', methods=['GET'])
def get_customer_problems():
    """Get active customer problems for dashboard display.
    
    Returns:
        JSON with formatted customer problems data including:
        - issue description, mentions, sentiment impact, priority level, status
    """
    try:
        from review_clustering.services.persistence_service import PersistenceService
        
        limit = request.args.get('limit', 10, type=int)
        
        # Get most recent run first
        recent_runs = PersistenceService.list_recent_runs(limit=1)
        
        if not recent_runs:
            return jsonify({
                "problems": [],
                "total_problems": 0,
                "last_updated": "2024-03-06T10:18:00Z"
            }), 200
        
        # Get the full run data including clusters
        latest_run_id = recent_runs[0].get("run_id")
        if not latest_run_id:
            return jsonify({
                "problems": [],
                "total_problems": 0,
                "last_updated": "2024-03-06T10:18:00Z"
            }), 200
        
        run_data = PersistenceService.get_run_by_id(latest_run_id)
        if not run_data:
            return jsonify({
                "problems": [],
                "total_problems": 0,
                "last_updated": "2024-03-06T10:18:00Z"
            }), 200
        
        clusters = run_data.get("clusters", [])
        
        # Format for dashboard display
        problems = []
        seen_labels = set()  # Track seen labels to avoid duplicates
        
        for cluster in clusters:
            # Convert cluster data to dashboard format
            label = cluster.get("label", "Unknown Issue").strip()
            
            # Skip if we've seen this label before (remove duplicates)
            if not label or label in seen_labels or label == "Unknown Issue":
                continue
                
            seen_labels.add(label)
            
            problem = {
                "issue_description": label,
                "sub_description": cluster.get("summary", ""),
                "mentions": cluster.get("frequency", 0),
                "sentiment_impact": round(cluster.get("avg_sentiment", 0) * 100, 1),
                "priority_level": get_priority_label(cluster.get("priority_score", 0)),
                "priority_score": cluster.get("priority_score", 0),
                "status": "pending" if cluster.get("priority_score", 0) > 0.7 else "in_progress",
                "representative_reviews": cluster.get("representative_reviews", [])
            }
            problems.append(problem)
        
        # Sort by priority score (highest first)
        problems.sort(key=lambda x: x.get("priority_score", 0), reverse=True)
        
        return jsonify({
            "problems": problems[:limit],  # Limit after deduplication
            "total_problems": len(problems),
            "last_updated": "2024-03-06T10:18:00Z"
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get customer problems: {str(e)}"}), 500


def get_priority_label(priority_score):
    """Convert numeric priority score to label."""
    if priority_score >= 0.8:
        return "High"
    elif priority_score >= 0.5:
        return "Medium"
    else:
        return "Low"


# ============================================================================
# SCHEDULED INGESTION
# ============================================================================

def scheduled_ingestion_task():
    """Background task that runs every hour to fetch and process reviews."""
    try:
        print("[Scheduler] Running periodic ingestion task...")
        
        # Get pending reviews
        pending = IngestionService.get_pending_reviews(100)
        if not pending:
            print("[Scheduler] No pending reviews")
            return
        
        items = []
        review_ids = []
        for review in pending:
            items.append({
                "text": review["review_text"],
                "timestamp": review["timestamp"]
            })
            review_ids.append(review["id"])
        
        # Run pipeline
        result = PipelineService.run_pipeline(items, save_to_db=True)
        IngestionService.mark_as_processed(review_ids)
        
        print(f"[Scheduler] Processed {len(review_ids)} reviews. "
              f"Clusters: {len(result.get('cluster_summary', {}))}. "
              f"Run ID: {result.get('run_id')}")
        
    except Exception as e:
        print(f"[Scheduler] Error: {str(e)}")


@app.route('/scheduler/start', methods=['POST'])
def start_scheduler():
    """Start the background scheduler for periodic ingestion."""
    global scheduler_started
    
    try:
        if scheduler_started and scheduler.running:
            return jsonify({"message": "Scheduler already running"}), 200
        
        scheduler.add_job(
            scheduled_ingestion_task,
            'interval',
            hours=1,
            id='periodic_ingestion',
            replace_existing=True
        )
        scheduler.start()
        scheduler_started = True
        
        return jsonify({"status": "Scheduler started", "interval_hours": 1}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/scheduler/stop', methods=['POST'])
def stop_scheduler():
    """Stop the background scheduler."""
    global scheduler_started
    
    try:
        if scheduler.running:
            scheduler.shutdown()
            scheduler_started = False
        return jsonify({"status": "Scheduler stopped"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/scheduler/status', methods=['GET'])
def scheduler_status():
    """Get scheduler status."""
    return jsonify({
        "running": scheduler.running if scheduler else False,
        "jobs": len(scheduler.get_jobs()) if scheduler else 0
    }), 200


# ============================================================================
# CONNECTOR MANAGEMENT ENDPOINTS
# ============================================================================

@app.route('/connectors', methods=['POST'])
def register_connector():
    """Register a new connector for review synchronization.
    
    Expected JSON:
    {
        "name": "my_app_google_play",
        "source_type": "google_play",  // or "app_store", "generic_api"
        "app_id": "com.example.myapp",
        "api_endpoint": "https://api.example.com/reviews",  // for generic_api
        "api_key": "your-api-key",
        "fetch_limit": 100,
        "fetch_interval_minutes": 60,
        "lookback_days": 7,
        "min_rating": 1,
        "max_rating": 5,
        "languages": ["en", "es"],
        "auth_type": "api_key",  // api_key, bearer, basic, oauth
        "extra_config": {}  // platform-specific settings
    }
    
    Returns:
        JSON with registration result
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body required"}), 400
        
        required_fields = ['name', 'source_type']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Create config
        config = ConnectorConfig(
            name=data['name'],
            source_type=data['source_type'],
            enabled=data.get('enabled', True),
            api_endpoint=data.get('api_endpoint'),
            api_key=data.get('api_key'),
            app_id=data.get('app_id'),
            product_id=data.get('product_id'),
            fetch_limit=data.get('fetch_limit', 100),
            fetch_interval_minutes=data.get('fetch_interval_minutes', 60),
            lookback_days=data.get('lookback_days', 7),
            min_rating=data.get('min_rating'),
            max_rating=data.get('max_rating'),
            languages=data.get('languages', []),
            auth_type=data.get('auth_type', 'api_key'),
            extra_config=data.get('extra_config', {}),
        )
        
        # Register with sync service
        sync_service = get_sync_service()
        connector = sync_service.register_connector_from_config(config)
        
        return jsonify({
            "status": "success",
            "message": f"Connector '{config.name}' registered",
            "connector": {
                "name": config.name,
                "source_type": config.source_type,
                "enabled": config.enabled,
            }
        }), 201
        
    except Exception as e:
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500


@app.route('/connectors', methods=['GET'])
def list_connectors():
    """List all registered connectors and their status."""
    try:
        sync_service = get_sync_service()
        connectors = []
        
        for name, connector in sync_service._connectors.items():
            status = connector.get_status()
            connectors.append({
                "name": name,
                "source_type": connector.config.source_type,
                "enabled": connector.config.enabled,
                "status": status,
            })
        
        return jsonify({
            "connectors": connectors,
            "total": len(connectors)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/connectors/<name>', methods=['GET'])
def get_connector(name):
    """Get detailed status of a specific connector."""
    try:
        sync_service = get_sync_service()
        connector = sync_service._connectors.get(name)
        
        if not connector:
            return jsonify({"error": f"Connector '{name}' not found"}), 404
        
        status = connector.get_status()
        
        return jsonify({
            "name": name,
            "source_type": connector.config.source_type,
            "enabled": connector.config.enabled,
            "config": {
                "app_id": connector.config.app_id,
                "api_endpoint": connector.config.api_endpoint,
                "fetch_limit": connector.config.fetch_limit,
                "fetch_interval_minutes": connector.config.fetch_interval_minutes,
                "lookback_days": connector.config.lookback_days,
            },
            "status": status,
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/connectors/<name>', methods=['DELETE'])
def remove_connector(name):
    """Remove a registered connector."""
    try:
        sync_service = get_sync_service()
        
        if name not in sync_service._connectors:
            return jsonify({"error": f"Connector '{name}' not found"}), 404
        
        del sync_service._connectors[name]
        
        # Also remove from scheduler if scheduled
        scheduler_service = get_scheduler_service()
        scheduler_service.remove_sync_job(name)
        
        return jsonify({
            "status": "success",
            "message": f"Connector '{name}' removed"
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/connectors/<name>/test', methods=['POST'])
def test_connector(name):
    """Test connection for a specific connector."""
    try:
        sync_service = get_sync_service()
        connector = sync_service._connectors.get(name)
        
        if not connector:
            return jsonify({"error": f"Connector '{name}' not found"}), 404
        
        success = connector.test_connection()
        
        return jsonify({
            "connector": name,
            "connection_successful": success,
            "status": connector.get_status(),
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# SYNC MANAGEMENT ENDPOINTS
# ============================================================================

@app.route('/sync', methods=['POST'])
def trigger_sync_all():
    """Trigger synchronization for all enabled connectors.
    
    Query params:
        - trigger_pipeline: bool (default: true) - Run NLP pipeline after sync
    
    Returns:
        JSON with sync results for each connector
    """
    try:
        trigger_pipeline = request.args.get('trigger_pipeline', 'true').lower() == 'true'
        
        sync_service = get_sync_service()
        results = sync_service.sync_all(trigger_pipeline=trigger_pipeline)
        
        response = []
        for result in results:
            response.append({
                "connector": result.connector_name,
                "success": result.success,
                "reviews_fetched": result.reviews_fetched,
                "reviews_stored": result.reviews_stored,
                "error": result.error_message,
                "duration_seconds": result.duration_seconds,
            })
        
        return jsonify({
            "status": "completed",
            "results": response,
            "total_connectors": len(results),
            "successful": sum(1 for r in results if r.success),
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Sync failed: {str(e)}"}), 500


@app.route('/sync/<connector_name>', methods=['POST'])
def trigger_sync_connector(connector_name):
    """Trigger synchronization for a specific connector.
    
    Query params:
        - trigger_pipeline: bool (default: true) - Run NLP pipeline after sync
    
    Returns:
        JSON with sync result
    """
    try:
        trigger_pipeline = request.args.get('trigger_pipeline', 'true').lower() == 'true'
        
        sync_service = get_sync_service()
        
        if connector_name not in sync_service._connectors:
            return jsonify({"error": f"Connector '{connector_name}' not found"}), 404
        
        result = sync_service.sync_connector(
            connector_name, 
            trigger_pipeline=trigger_pipeline
        )
        
        # Calculate duration
        duration = None
        if result.completed_at and result.started_at:
            duration = (result.completed_at - result.started_at).total_seconds()
        
        return jsonify({
            "status": "completed",
            "connector": result.connector_name,
            "success": result.success,
            "reviews_fetched": result.reviews_fetched,
            "reviews_stored": result.reviews_stored,
            "duplicates_skipped": result.reviews_duplicate,
            "error": result.error_message,
            "duration_seconds": duration,
            "pipeline_triggered": result.pipeline_triggered,
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Sync failed: {str(e)}"}), 500


@app.route('/sync/history', methods=['GET'])
def get_sync_history():
    """Get history of sync jobs.
    
    Query params:
        - connector: str (optional) - Filter by connector name
        - limit: int (default: 50) - Number of records to return
    
    Returns:
        JSON with sync job history
    """
    try:
        connector = request.args.get('connector')
        limit = request.args.get('limit', 50, type=int)
        
        sync_service = get_sync_service()
        history = sync_service.get_sync_history(
            connector_name=connector,
            limit=limit
        )
        
        return jsonify({
            "history": history,
            "total": len(history),
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/sync/stats', methods=['GET'])
def get_sync_stats():
    """Get synchronization statistics."""
    try:
        sync_service = get_sync_service()
        stats = sync_service.get_sync_stats()
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# AUTOMATED SYNC SCHEDULER ENDPOINTS
# ============================================================================

@app.route('/scheduler/sync/start', methods=['POST'])
def start_sync_scheduler():
    """Start the automated review sync scheduler.
    
    This starts the background scheduler that will automatically
    fetch reviews from all configured connectors at their specified intervals.
    """
    try:
        scheduler_service = get_scheduler_service()
        
        if scheduler_service.is_running:
            return jsonify({
                "message": "Sync scheduler already running",
                "status": scheduler_service.get_status()
            }), 200
        
        scheduler_service.start()
        
        return jsonify({
            "status": "started",
            "message": "Automated sync scheduler started",
            "scheduler_status": scheduler_service.get_status()
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/scheduler/sync/stop', methods=['POST'])
def stop_sync_scheduler():
    """Stop the automated review sync scheduler."""
    try:
        scheduler_service = get_scheduler_service()
        scheduler_service.shutdown()
        
        return jsonify({
            "status": "stopped",
            "message": "Automated sync scheduler stopped"
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/scheduler/sync/status', methods=['GET'])
def sync_scheduler_status():
    """Get automated sync scheduler status."""
    try:
        scheduler_service = get_scheduler_service()
        status = scheduler_service.get_status()
        
        return jsonify(status), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/scheduler/sync/jobs', methods=['GET'])
def get_sync_jobs():
    """Get list of scheduled sync jobs."""
    try:
        scheduler_service = get_scheduler_service()
        jobs = scheduler_service.get_scheduled_jobs()
        
        return jsonify({
            "jobs": jobs,
            "total": len(jobs),
            "running": scheduler_service.get_running_jobs(),
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/scheduler/sync/jobs', methods=['POST'])
def add_sync_job():
    """Add a new scheduled sync job.
    
    Expected JSON:
    {
        "connector_name": "my_app_google_play",
        "interval_minutes": 60,  // OR
        "cron_expression": "0 * * * *",
        "start_hour": 8,  // optional - only run between these hours
        "end_hour": 22,
        "trigger_pipeline": true
    }
    """
    try:
        data = request.get_json()
        if not data or 'connector_name' not in data:
            return jsonify({"error": "connector_name is required"}), 400
        
        connector_name = data['connector_name']
        interval_minutes = data.get('interval_minutes')
        cron_expression = data.get('cron_expression')
        
        if not interval_minutes and not cron_expression:
            return jsonify({
                "error": "Either interval_minutes or cron_expression is required"
            }), 400
        
        # Verify connector exists
        sync_service = get_sync_service()
        if connector_name not in sync_service._connectors:
            return jsonify({
                "error": f"Connector '{connector_name}' not found. Register it first."
            }), 404
        
        scheduler_service = get_scheduler_service()
        job_id = scheduler_service.add_sync_job(
            connector_name=connector_name,
            interval_minutes=interval_minutes,
            cron_expression=cron_expression,
            start_hour=data.get('start_hour'),
            end_hour=data.get('end_hour'),
            trigger_pipeline=data.get('trigger_pipeline', True),
        )
        
        return jsonify({
            "status": "success",
            "message": f"Sync job added for '{connector_name}'",
            "job_id": job_id,
            "interval_minutes": interval_minutes,
            "cron_expression": cron_expression,
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/scheduler/sync/jobs/<connector_name>', methods=['DELETE'])
def remove_sync_job_endpoint(connector_name):
    """Remove a scheduled sync job."""
    try:
        scheduler_service = get_scheduler_service()
        removed = scheduler_service.remove_sync_job(connector_name)
        
        if removed:
            return jsonify({
                "status": "success",
                "message": f"Sync job for '{connector_name}' removed"
            }), 200
        else:
            return jsonify({
                "error": f"No sync job found for '{connector_name}'"
            }), 404
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/scheduler/sync/jobs/<connector_name>/trigger', methods=['POST'])
def trigger_sync_job_now(connector_name):
    """Trigger an immediate execution of a sync job."""
    try:
        trigger_pipeline = request.args.get('trigger_pipeline', 'true').lower() == 'true'
        
        scheduler_service = get_scheduler_service()
        result = scheduler_service.trigger_sync_now(
            connector_name,
            trigger_pipeline=trigger_pipeline
        )
        
        if result is None:
            return jsonify({
                "error": f"Sync already running for '{connector_name}'"
            }), 409
        
        return jsonify({
            "status": "completed",
            "connector": result.connector_name,
            "success": result.success,
            "reviews_fetched": result.reviews_fetched,
            "reviews_stored": result.reviews_stored,
            "error": result.error_message,
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# HEALTH & INFO ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"}), 200


@app.route('/info', methods=['GET'])
def info():
    """API information and available endpoints."""
    return jsonify({
        "service": "Review Clustering Pipeline",
        "version": "2.0.0",
        "endpoints": {
            "ingestion": {
                "POST /upload-csv": "Upload reviews from CSV file",
                "POST /ingest-api": "Ingest reviews from JSON API",
                "GET /ingestion-status": "Get recent ingestion job history"
            },
            "processing": {
                "POST /process-reviews": "Process pending reviews through pipeline",
                "GET /cluster-results/<run_id>": "Get clustering results for a run",
                "GET /top-clusters": "Get highest priority clusters",
                "GET /customer-problems": "Get formatted customer problems for dashboard"
            },
            "connectors": {
                "POST /connectors": "Register a new connector",
                "GET /connectors": "List all registered connectors",
                "GET /connectors/<name>": "Get connector details",
                "DELETE /connectors/<name>": "Remove a connector",
                "POST /connectors/<name>/test": "Test connector connection"
            },
            "sync": {
                "POST /sync": "Sync all connectors",
                "POST /sync/<connector>": "Sync specific connector",
                "GET /sync/history": "Get sync job history",
                "GET /sync/stats": "Get sync statistics"
            },
            "scheduler": {
                "POST /scheduler/start": "Start periodic processing (hourly)",
                "POST /scheduler/stop": "Stop periodic processing",
                "GET /scheduler/status": "Get scheduler status"
            },
            "automated_sync": {
                "POST /scheduler/sync/start": "Start automated sync scheduler",
                "POST /scheduler/sync/stop": "Stop automated sync scheduler",
                "GET /scheduler/sync/status": "Get sync scheduler status",
                "GET /scheduler/sync/jobs": "List scheduled sync jobs",
                "POST /scheduler/sync/jobs": "Add a scheduled sync job",
                "DELETE /scheduler/sync/jobs/<name>": "Remove a sync job",
                "POST /scheduler/sync/jobs/<name>/trigger": "Trigger sync now"
            }
        }
    }), 200


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    # In development only - use Gunicorn in production
    print("Starting Review Clustering Pipeline API...")
    print("Available at http://localhost:5000")
    print("API docs at http://localhost:5000/info")
    app.run(debug=True, host='0.0.0.0', port=5000)
