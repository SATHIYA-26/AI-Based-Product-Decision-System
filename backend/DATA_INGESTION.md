# Data Ingestion Layer - Complete Guide

## Overview

The data ingestion layer enables review collection from multiple sources (CSV, API, scheduled imports) with automatic deduplication, validation, and integration with the clustering pipeline.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   DATA SOURCES                              │
├─────────────────┬─────────────────┬─────────────────────────┤
│   CSV Upload    │   JSON API      │   Scheduled Cron        │
└────────┬────────┴────────┬────────┴──────────────┬──────────┘
         │                 │                       │
         └─────────────────┴───────────────────────┘
                      │
         ┌────────────▼────────────┐
         │  IngestionService       │
         │  - Parse/validate       │
         │  - Dedup check          │
         │  - Store to DB          │
         └────────────┬────────────┘
                      │
         ┌────────────▼────────────┐
         │   RawReview Table       │
         │   (Ingestion Queue)     │
         │                         │
         │  source, text, rating   │
         │  author, timestamp      │
         └────────────┬────────────┘
                      │
         ┌────────────▼────────────┐
         │  Pipeline Service       │
         │  - Filter              │
         │  - Preprocess          │
         │  - Cluster             │
         │  - Score               │
         └────────────┬────────────┘
                      │
         ┌────────────▼────────────┐
         │  ClusterResult Table    │
         │  (Analysis Results)     │
         └────────────────────────┘
```

## Database Schema

### RawReview Table
Stores unprocessed reviews from any source.

```sql
CREATE TABLE raw_reviews (
    id INTEGER PRIMARY KEY,
    source VARCHAR(50),          -- 'csv', 'api', 'play_store', etc.
    source_id VARCHAR(100),      -- External ID from source
    review_text TEXT,
    rating FLOAT,
    author VARCHAR(255),
    timestamp DATETIME,
    extra_data VARCHAR(1000),    -- JSON for extra metadata
    is_duplicate BOOLEAN,
    ingested_at DATETIME
);
```

### IngestionJob Table
Tracks the status and metrics of each ingestion operation.

```sql
CREATE TABLE ingestion_jobs (
    id INTEGER PRIMARY KEY,
    job_type VARCHAR(50),        -- 'csv_upload', 'api_import', 'scheduled'
    source VARCHAR(50),
    status VARCHAR(20),          -- 'pending', 'running', 'completed', 'failed'
    total_records INTEGER,
    successful INTEGER,
    failed INTEGER,
    duplicates_found INTEGER,
    error_message VARCHAR(500),
    started_at DATETIME,
    completed_at DATETIME
);
```

## Usage Examples

### 1. CSV Upload

**File Format:**
```csv
review_text,rating,author,timestamp
Login failed after update,1,john_doe,2026-02-27T10:00:00
Payment processing error,1,jane_smith,2026-02-27T10:30:00
```

**Python:**
```python
from app.services.ingestion_service import IngestionService

csv_content = open('reviews.csv').read()
result = IngestionService.ingest_csv(csv_content, source="play_store")
# Returns: {job_id, source, total, successful, failed, duplicates, status}
```

**cURL:**
```bash
curl -X POST \
  -F "file=@reviews.csv" \
  -F "source=app_store" \
  http://localhost:5000/upload-csv
```

---

### 2. API Ingestion

**Expected Payload:**
```json
{
  "reviews": [
    {
      "text": "App crashes on startup",
      "rating": 1,
      "author": "user123",
      "timestamp": "2026-02-27T10:00:00",
      "source_id": "review_12345"
    }
  ],
  "source": "twitter"
}
```

**Python:**
```python
from app.services.ingestion_service import IngestionService

reviews = [
  {"text": "Login not working", "rating": 1},
  {"text": "Good app", "rating": 5}
]
result = IngestionService.ingest_api(reviews, source="support_tickets")
```

**cURL:**
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "reviews": [{"text": "App crashes", "rating": 1}],
    "source": "app_store"
  }' \
  http://localhost:5000/ingest-api
```

---

### 3. Scheduled Ingestion (Hourly)

The Flask app includes APScheduler for automatic periodic processing.

**Start Scheduler:**
```bash
curl -X POST http://localhost:5000/scheduler/start
```

**Check Status:**
```bash
curl http://localhost:5000/scheduler/status
```

**Stop Scheduler:**
```bash
curl -X POST http://localhost:5000/scheduler/stop
```

Or in Python:
```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(
    process_pending_reviews,
    'interval',
    hours=1  # Run every hour
)
scheduler.start()
```

---

## Processing Pipeline

Once reviews are ingested, process them through clustering:

**Python:**
```python
from app.services.pipeline_service import PipelineService

# Get pending reviews
pending = IngestionService.get_pending_reviews(limit=1000)

# Prepare for pipeline
items = [{"text": r["review_text"], "timestamp": r["timestamp"]} 
         for r in pending]

# Run clustering
result = PipelineService.run_pipeline(items, save_to_db=True)

# Mark as processed
IngestionService.mark_as_processed([r["id"] for r in pending])
```

**cURL:**
```bash
curl -X POST http://localhost:5000/process-reviews?limit=100
```

---

## Features

✅ **Multiple Ingestion Sources**
- CSV file upload
- JSON API endpoint
- Scheduled/cron-based imports

✅ **Data Quality**
- Automatic validation
- Duplicate detection across sources
- Empty text filtering
- Rating normalization

✅ **Audit Trail**
- Complete job history
- Ingestion metrics
- Error tracking
- Timestamp recording

✅ **Integration**
- Seamless pipeline integration
- Deferred processing queue
- Async scheduling support

✅ **Scalability**
- Batch processing
- Configurable limits
- Job status tracking
- Metrics logging

---

## Flask API Endpoints

### Ingestion
```
POST   /upload-csv           Upload CSV file with reviews
POST   /ingest-api           Ingest reviews from JSON
GET    /ingestion-status     View job history
```

### Processing
```
POST   /process-reviews      Run pipeline on pending reviews
GET    /cluster-results/{id} Get clustering results
GET    /top-clusters         Get highest priority clusters
```

### Scheduler
```
POST   /scheduler/start      Enable hourly processing
POST   /scheduler/stop       Disable scheduler
GET    /scheduler/status     Check scheduler status
```

### Health
```
GET    /health               Health check
GET    /info                 API documentation
```

---

## Configuration

**Change scheduler interval:**
```python
# In app/main.py
scheduler.add_job(
    scheduled_ingestion_task,
    'interval',
    hours=1,  # Change this (also support: minutes, seconds)
    id='periodic_ingestion'
)
```

**Change batch processing limit:**
```python
# In Flask route
pending = IngestionService.get_pending_reviews(limit=500)  # Default: 1000
```

**Connect to different database:**
```python
# In app/models/ingestion.py
def get_ingestion_db_session(
    db_url="postgresql://user:pass@localhost/cluster_db"
):
    ...
```

---

## Running the System

1. **Start Flask server:**
```bash
cd D:\AI\backend
python app/main.py
```

2. **Upload reviews:**
```bash
curl -X POST -F "file=@reviews.csv" http://localhost:5000/upload-csv
```

3. **Process them:**
```bash
curl -X POST http://localhost:5000/process-reviews
```

4. **Enable automatic processing:**
```bash
curl -X POST http://localhost:5000/scheduler/start
```

5. **Check results:**
```bash
curl http://localhost:5000/top-clusters?limit=10
```

---

## Testing

Run the complete test suite:
```bash
python test_ingestion.py    # Unit tests (no server needed)
```

Test the Flask API (requires running server):
```bash
python test_api.py
```

---

## Production Deployment

For production:

1. **Use Gunicorn instead of Flask dev server:**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app.main:app
```

2. **Use a production database (PostgreSQL):**
```python
db_url = "postgresql://prod_user:password@db.example.com/cluster_db"
```

3. **Enable scheduled processing with Celery:**
```bash
celery -A app.workers.tasks worker --loglevel=info
```

4. **Use Docker for containerization** (create Dockerfile)

---

## Supported File Sources

The system can ingest reviews from:

| Source | Method | Example |
|--------|--------|---------|
| CSV file | Upload | `POST /upload-csv` |
| JSON API | POST | `POST /ingest-api` |
| Scheduled cron | Background | `hourly` |
| Play Store | API batching | `POST /ingest-api` |
| App Store | API batching | `POST /ingest-api` |
| Twitter | Streaming API | Custom scheduler |
| Support Tickets | DB sync | Custom scheduler |
| Amazon | API polling | Custom scheduler |

---

## Next Steps

1. ✅ Data ingestion layer (DONE)
2. ⏭️ Add email alerts for high-priority issues
3. ⏭️ Add webhook notifications
4. ⏭️ Add dashboard/web UI
5. ⏭️ Add analytics (trends, heatmaps)
6. ⏭️ Deploy to production (Docker, K8s)
