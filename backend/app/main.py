"""Flask application with REST endpoints for ingestion and clustering."""

from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from apscheduler.schedulers.background import BackgroundScheduler
import os
import json

from app.services.ingestion_service import IngestionService
from app.services.pipeline_service import PipelineService

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), '..', 'uploads')

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
        from app.services.persistence_service import PersistenceService
        
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
        from app.services.persistence_service import PersistenceService
        
        limit = request.args.get('limit', 10, type=int)
        clusters = PersistenceService.get_clusters_by_priority(limit)
        return jsonify({"clusters": clusters}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
        "version": "1.0.0",
        "endpoints": {
            "ingestion": {
                "POST /upload-csv": "Upload reviews from CSV file",
                "POST /ingest-api": "Ingest reviews from JSON API",
                "GET /ingestion-status": "Get recent ingestion job history"
            },
            "processing": {
                "POST /process-reviews": "Process pending reviews through pipeline",
                "GET /cluster-results/<run_id>": "Get clustering results for a run",
                "GET /top-clusters": "Get highest priority clusters"
            },
            "scheduler": {
                "POST /scheduler/start": "Start periodic processing (hourly)",
                "POST /scheduler/stop": "Stop periodic processing",
                "GET /scheduler/status": "Get scheduler status"
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
