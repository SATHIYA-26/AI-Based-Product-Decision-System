# Automated Review Synchronization System

This document describes the automated review ingestion mechanism that periodically retrieves product reviews from external sources and processes them through the NLP clustering pipeline.

## Overview

The Automated Sync System provides:

- **Connector Layer**: Abstraction for fetching reviews from various sources
- **Sync Service**: Orchestrates review fetching, storage, and pipeline triggering
- **Scheduler Service**: Automates periodic synchronization with configurable intervals
- **REST API**: Endpoints for managing connectors, triggering syncs, and monitoring

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         External Review Sources                              │
├─────────────────┬─────────────────┬────────────────┬────────────────────────┤
│  Google Play    │   App Store     │  Custom APIs   │  Support Systems       │
│    (RSS/API)    │   (RSS/API)     │  (REST/SOAP)   │  (Zendesk, etc.)       │
└────────┬────────┴────────┬────────┴───────┬────────┴───────────┬────────────┘
         │                 │                │                    │
         ▼                 ▼                ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Connector Layer                                     │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────────────────┐│
│  │ GooglePlay      │ │ AppStore        │ │ GenericAPIConnector             ││
│  │ Connector       │ │ Connector       │ │ (Configurable field mapping)    ││
│  └────────┬────────┘ └────────┬────────┘ └────────────────┬────────────────┘│
│           │                   │                           │                  │
│           └───────────────────┼───────────────────────────┘                  │
│                               ▼                                              │
│                    ┌─────────────────────┐                                   │
│                    │ ReviewSyncService   │                                   │
│                    │ (Orchestrator)      │                                   │
│                    └──────────┬──────────┘                                   │
└───────────────────────────────┼──────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│                        IngestionService                                        │
│                   (Deduplication, Validation)                                  │
└───────────────────────────────┬───────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│                          RawReview Table                                       │
│                    (source, source_id, text, rating, ...)                      │
└───────────────────────────────┬───────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│                         PipelineService                                        │
│  (Preprocessing → Embedding → Clustering → Sentiment → Priority → Sampling)   │
└───────────────────────────────┬───────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│                        ClusterResult Table                                     │
│               (Clusters with labels, priorities, trends)                       │
└───────────────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Base Connector (`connectors/base_connector.py`)

All connectors implement this abstract base class:

```python
from review_clustering.connectors import BaseConnector, ReviewData, ConnectorConfig

class MyConnector(BaseConnector):
    def fetch_reviews(self, since=None, limit=100) -> FetchResult:
        # Fetch reviews from source
        pass
    
    def test_connection(self) -> bool:
        # Verify connectivity
        pass
    
    def validate_config(self) -> List[str]:
        # Return list of config errors
        pass
```

**Key Data Classes:**

```python
@dataclass
class ReviewData:
    text: str
    rating: Optional[int] = None
    author: Optional[str] = None
    timestamp: Optional[datetime] = None
    source_id: Optional[str] = None
    source: Optional[str] = None
    language: Optional[str] = None
    app_version: Optional[str] = None
    device: Optional[str] = None
    extra_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ConnectorConfig:
    name: str
    source_type: str  # google_play, app_store, generic_api
    enabled: bool = True
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    app_id: Optional[str] = None
    fetch_limit: int = 100
    fetch_interval_minutes: int = 60
    lookback_days: int = 7
    # ... more options
```

### 2. Platform Connectors

#### Google Play Connector (`connectors/google_play_connector.py`)

```python
from review_clustering.connectors import GooglePlayConnector, ConnectorConfig

config = ConnectorConfig(
    name="my_app_google_play",
    source_type="google_play",
    app_id="com.example.myapp",
    fetch_limit=200,
    lookback_days=7,
    extra_config={
        "language": "en",
        "country": "us"
    }
)

connector = GooglePlayConnector(config)
result = connector.fetch_reviews()
print(f"Fetched {len(result.reviews)} reviews")
```

#### App Store Connector (`connectors/app_store_connector.py`)

```python
from review_clustering.connectors import AppStoreConnector, ConnectorConfig

config = ConnectorConfig(
    name="my_app_app_store",
    source_type="app_store",
    app_id="123456789",  # App Store numeric ID
    extra_config={
        "country": "us"
    }
)

connector = AppStoreConnector(config)
```

#### Generic API Connector (`connectors/generic_api_connector.py`)

For custom REST APIs:

```python
from review_clustering.connectors import GenericAPIConnector, ConnectorConfig

config = ConnectorConfig(
    name="internal_reviews",
    source_type="generic_api",
    api_endpoint="https://api.company.com/reviews",
    api_key="your-api-key",
    auth_type="bearer",  # api_key, bearer, basic, oauth
    extra_config={
        "field_mapping": {
            "text": "review_body",
            "rating": "star_rating",
            "author": "user.name",
            "timestamp": "created_at",
            "source_id": "review_id"
        },
        "pagination_style": "offset",  # offset, cursor, page
        "reviews_path": "data.reviews"
    }
)
```

### 3. Sync Service (`services/sync_service.py`)

Central orchestrator for synchronization:

```python
from review_clustering.services.sync_service import get_sync_service

sync_service = get_sync_service()

# Register connectors
sync_service.register_connector_from_config(google_play_config)
sync_service.register_connector_from_config(app_store_config)

# Sync all connectors
results = sync_service.sync_all(trigger_pipeline=True)

# Sync specific connector
result = sync_service.sync_connector("my_app_google_play")

# Get history and stats
history = sync_service.get_sync_history(limit=100)
stats = sync_service.get_sync_stats()
```

### 4. Scheduler Service (`services/scheduler_service.py`)

Automated scheduling with APScheduler:

```python
from review_clustering.services.scheduler_service import (
    get_scheduler_service, start_automated_sync
)

# Quick setup
start_automated_sync([
    {
        'name': 'app_google_play',
        'source_type': 'google_play',
        'app_id': 'com.example.app',
        'interval_minutes': 30,
    },
    {
        'name': 'app_app_store',
        'source_type': 'app_store',
        'app_id': '123456789',
        'interval_minutes': 60,
    },
])

# Or manual setup
scheduler = get_scheduler_service()

# Add jobs
scheduler.add_sync_job(
    connector_name="my_app_google_play",
    interval_minutes=60,
    start_hour=8,   # Only run between 8am-10pm
    end_hour=22,
)

# Add cron-based job
scheduler.add_sync_job(
    connector_name="my_app_app_store",
    cron_expression="0 */2 * * *",  # Every 2 hours
)

# Start scheduler
scheduler.start()

# Monitor
status = scheduler.get_status()
jobs = scheduler.get_scheduled_jobs()
```

## REST API Endpoints

### Connector Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/connectors` | Register a new connector |
| GET | `/connectors` | List all registered connectors |
| GET | `/connectors/<name>` | Get connector details |
| DELETE | `/connectors/<name>` | Remove a connector |
| POST | `/connectors/<name>/test` | Test connector connection |

**Register a connector:**
```bash
curl -X POST http://localhost:5000/connectors \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my_app_google_play",
    "source_type": "google_play",
    "app_id": "com.example.myapp",
    "fetch_limit": 100,
    "fetch_interval_minutes": 60
  }'
```

### Sync Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sync` | Sync all connectors |
| POST | `/sync/<connector>` | Sync specific connector |
| GET | `/sync/history` | Get sync job history |
| GET | `/sync/stats` | Get sync statistics |

**Trigger sync:**
```bash
# Sync all connectors
curl -X POST http://localhost:5000/sync

# Sync specific connector
curl -X POST http://localhost:5000/sync/my_app_google_play

# Sync without triggering pipeline
curl -X POST "http://localhost:5000/sync?trigger_pipeline=false"
```

### Automated Scheduler

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/scheduler/sync/start` | Start automated scheduler |
| POST | `/scheduler/sync/stop` | Stop automated scheduler |
| GET | `/scheduler/sync/status` | Get scheduler status |
| GET | `/scheduler/sync/jobs` | List scheduled jobs |
| POST | `/scheduler/sync/jobs` | Add a scheduled job |
| DELETE | `/scheduler/sync/jobs/<name>` | Remove a job |
| POST | `/scheduler/sync/jobs/<name>/trigger` | Trigger job immediately |

**Add a scheduled job:**
```bash
curl -X POST http://localhost:5000/scheduler/sync/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "connector_name": "my_app_google_play",
    "interval_minutes": 30,
    "start_hour": 8,
    "end_hour": 22
  }'
```

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# External Connector Configuration
GOOGLE_PLAY_APP_ID=com.example.yourapp
GOOGLE_PLAY_LANGUAGE=en
GOOGLE_PLAY_COUNTRY=us

APP_STORE_APP_ID=123456789
APP_STORE_COUNTRY=us

CUSTOM_API_ENDPOINT=https://api.example.com/reviews
CUSTOM_API_KEY=your-api-key
CUSTOM_API_AUTH_TYPE=api_key

# Automated Sync Configuration
SYNC_FETCH_LIMIT=100
SYNC_LOOKBACK_DAYS=7
SYNC_MAX_CONCURRENT_JOBS=3
SYNC_DEFAULT_INTERVAL_MINUTES=60
SYNC_START_HOUR=8
SYNC_END_HOUR=22
```

## Database Models

The sync system adds these models:

- **ConnectorConfiguration**: Stores connector settings for persistence
- **SyncJob**: Records sync job executions with metrics
- **SyncSchedule**: Scheduling configuration for each connector

```sql
-- Example queries
SELECT * FROM connector_configuration WHERE enabled = true;
SELECT * FROM sync_job ORDER BY started_at DESC LIMIT 10;
SELECT * FROM sync_schedule WHERE is_active = true;
```

## Usage Examples

### Complete Setup Example

```python
from review_clustering.connectors import ConnectorConfig
from review_clustering.services.sync_service import get_sync_service
from review_clustering.services.scheduler_service import get_scheduler_service

# 1. Configure connectors
google_play = ConnectorConfig(
    name="myapp_google_play",
    source_type="google_play",
    app_id="com.company.myapp",
    fetch_limit=200,
    fetch_interval_minutes=30,
    lookback_days=7,
)

app_store = ConnectorConfig(
    name="myapp_app_store",
    source_type="app_store",
    app_id="123456789",
    fetch_limit=100,
    fetch_interval_minutes=60,
)

# 2. Register with sync service
sync_service = get_sync_service()
sync_service.register_connector_from_config(google_play)
sync_service.register_connector_from_config(app_store)

# 3. Setup automated scheduling
scheduler = get_scheduler_service()

scheduler.add_sync_job(
    "myapp_google_play",
    interval_minutes=30,
    start_hour=8,
    end_hour=22,
)

scheduler.add_sync_job(
    "myapp_app_store",
    interval_minutes=60,
)

# 4. Start automation
scheduler.start()

# 5. Monitor
print(scheduler.get_status())
print(scheduler.get_scheduled_jobs())
```

### Manual Sync with Flask App

```bash
# Start Flask server
python run.py

# Register connectors
curl -X POST http://localhost:5000/connectors -H "Content-Type: application/json" \
  -d '{"name": "gp", "source_type": "google_play", "app_id": "com.example.app"}'

# Trigger sync
curl -X POST http://localhost:5000/sync/gp

# Check history
curl http://localhost:5000/sync/history
```

## Error Handling

The sync system includes comprehensive error handling:

- **Connection failures**: Logged and tracked in sync history
- **Rate limiting**: Respects API rate limits with configurable delays
- **Deduplication**: Automatic duplicate detection using source_id
- **Retry logic**: Failed syncs can be retried with exponential backoff
- **Partial success**: Stores successfully fetched reviews even if pipeline fails

## Best Practices

1. **Start with conservative intervals** (60+ minutes) and adjust based on review volume
2. **Use execution windows** to avoid overnight processing
3. **Monitor sync statistics** to detect API issues early
4. **Set appropriate fetch limits** to balance freshness vs. API costs
5. **Store API keys securely** using environment variables
6. **Test connectors** before enabling automated scheduling

## Troubleshooting

### No reviews being fetched?
- Verify app_id is correct
- Check connector test endpoint: `POST /connectors/<name>/test`
- Review logs for API errors

### Duplicate reviews?
- Normal - deduplication uses `source_id` field
- Check `duplicates_skipped` in sync results

### Pipeline not triggering?
- Ensure `trigger_pipeline=true` in sync call
- Check for unprocessed reviews: `GET /ingestion-status`

### Scheduler not running?
- Start it: `POST /scheduler/sync/start`
- Check status: `GET /scheduler/sync/status`
