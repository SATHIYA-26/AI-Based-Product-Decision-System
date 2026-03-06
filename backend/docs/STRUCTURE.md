# Project Structure

This document describes the organization of the Review Clustering System project.

## Directory Layout

```
backend/
├── src/                              # Main source code
│   ├── __init__.py                  # Package initialization
│   └── review_clustering/           # Main application package
│       ├── __init__.py
│       ├── main.py                  # Flask application entry point
│       ├── api/                     # API-related modules (reserved)
│       ├── services/                # Business logic services
│       │   ├── __init__.py
│       │   ├── ingestion_service.py # CSV/API data ingestion
│       │   ├── pipeline_service.py  # Main clustering pipeline orchestration
│       │   ├── persistence_service.py # Database operations
│       │   ├── preprocessing_service.py # Text preprocessing (Spacy)
│       │   ├── embedding_service.py # Text vectorization
│       │   ├── clustering_service.py # HDBSCAN clustering
│       │   ├── sentiment_service.py # Sentiment analysis (VADER)
│       │   ├── priority_service.py  # Priority score computation
│       │   ├── sampling_service.py  # Representative review selection
│       │   ├── data_filter_service.py # Review filtering and validation
│       │   ├── trend_service.py     # Weekly trend calculation
│       │   └── llm_service.py       # OpenAI integration
│       ├── models/                  # SQLAlchemy database models
│       │   ├── __init__.py
│       │   ├── cluster_analysis.py  # ClusterResult and PipelineRun models
│       │   └── ingestion.py         # RawReview and IngestionJob models
│       ├── core/                    # Core configuration (reserved)
│       ├── database/                # Database utilities (reserved)
│       └── workers/                 # Background task workers
│           ├── __init__.py
│           └── tasks.py             # Celery tasks (placeholder)
│
├── tests/                           # Test suite
│   ├── __init__.py
│   ├── test_ingestion.py           # Ingestion layer tests
│   ├── test_api.py                 # API endpoint tests
│   ├── test_complete_system.py     # Integration tests
│   ├── test_persistence.py         # Database tests
│   └── test.py                     # Original pipeline tests
│
├── data/                            # Data and database files
│   └── cluster_analysis.db         # SQLite database (created on first run)
│
├── docs/                            # Project documentation
│   ├── DATA_INGESTION.md           # Data ingestion layer guide
│   ├── README.md                   # Project overview
│   ├── STRUCTURE.md                # This file
│   └── API.md                      # API documentation (coming soon)
│
├── config/                          # Configuration modules
│   ├── __init__.py
│   └── config.py                   # Environment-based configuration
│
├── uploads/                         # Temporary file uploads directory
│   └── (CSV files from /upload-csv endpoint)
│
├── logs/                            # Application logs (created on first run)
│   └── app.log                     # Main application log
│
├── ROOT FILES (APPLICATION ENTRY POINTS & CONFIG)
├── run.py                           # Flask development server launcher
├── setup.py                         # Python package setup
├── pyproject.toml                  # Modern Python project configuration
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore rules
├── .env                            # Environment variables (local, not in git)
├── README.md                       # Project overview
├── CHANGELOG.md                    # Version history and changes
├── Dockerfile                      # Docker container definition
└── docker-compose.yml              # Docker Compose orchestration
```

## Module Descriptions

### `src/review_clustering/main.py`
The Flask application with REST endpoints:
- **POST /upload-csv** - Upload reviews from CSV
- **POST /ingest-api** - Ingest reviews from JSON API
- **POST /process-reviews** - Trigger clustering pipeline
- **GET /cluster-results/{id}** - Retrieve specific cluster analysis
- **GET /top-clusters** - Get high-priority clusters
- **POST /scheduler/{start|stop}** - Manage automatic processing
- **GET /scheduler/status** - Check scheduler status
- **GET /ingestion-status** - Check ingestion queue
- **GET /health** - Health check
- **GET /info** - System information

### Services Layer (`src/review_clustering/services/`)

Each service handles a specific responsibility:

| Service | Purpose |
|---------|---------|
| `ingestion_service.py` | CSV parsing, JSON API handling, deduplication |
| `pipeline_service.py` | Orchestrates the complete clustering workflow |
| `persistence_service.py` | Database save/retrieve operations |
| `preprocessing_service.py` | Spacy-based NLP preprocessing |
| `embedding_service.py` | Text vectorization using scikit-learn |
| `clustering_service.py` | HDBSCAN clustering algorithm |
| `sentiment_service.py` | VADER sentiment analysis |
| `priority_service.py` | Multi-factor priority scoring |
| `sampling_service.py` | Representative review selection |
| `data_filter_service.py` | Filtering junk and short reviews |
| `trend_service.py` | Weekly growth trend detection |
| `llm_service.py` | OpenAI API for summaries/labels |

### Models Layer (`src/review_clustering/models/`)

SQLAlchemy ORM models for database persistence:

| Model | Purpose |
|-------|---------|
| `ClusterResult` | Stores cluster analysis results |
| `PipelineRun` | Records pipeline execution metadata |
| `RawReview` | Queue of ingested reviews awaiting processing |
| `IngestionJob` | Audit trail of ingestion operations |

### Test Suite (`tests/`)

Comprehensive test coverage:
- **test_ingestion.py** - Data ingestion layer
- **test_api.py** - REST endpoint testing
- **test_complete_system.py** - End-to-end integration tests
- **test_persistence.py** - Database operations
- **test.py** - Original pipeline validation

Run with: `python -m pytest tests/ -v`

### Configuration (`config/`)

Centralized configuration management:
- Reads from `.env` file (see `.env.example`)
- Environment variable fallbacks
- Feature flags for enabling/disabling features
- Database URL configuration
- Logging and scheduler settings

## Data Flow

```
CSV Upload / API Ingestion
        ↓
IngestionService (Parse, Validate, Deduplicate)
        ↓
RawReview Table (Queue)
        ↓
PipelineService (Orchestration)
        ├→ DataFilterService (Remove junk/short reviews)
        ├→ PreprocessingService (Spacy NLP)
        ├→ EmbeddingService (Text vectorization)
        ├→ ClusteringService (HDBSCAN)
        ├→ SentimentService (VADER analysis)
        ├→ PriorityService (Score computation)
        ├→ SamplingService (Select representatives)
        ├→ TrendService (Weekly growth)
        └→ LLMService (Summaries/labels - optional)
        ↓
PersistenceService (Save results)
        ↓
ClusterResult / PipelineRun Tables
        ↓
REST API (Retrieve & expose results)
```

## Key Features by Component

### Ingestion System
- Multi-source support (CSV, JSON API, scheduled)
- Automatic deduplication
- Validation and error handling
- Audit trail via IngestionJob table

### Processing Pipeline
- 11-stage processing workflow
- Graceful error handling
- Optional LLM enrichment
- Configurable clustering parameters

### Storage
- SQLite for development
- PostgreSQL ready for production
- Full audit trail
- Efficient querying

### API
- RESTful design
- JSON request/response
- Error handling
- Health checks

## Configuration Files

### `.env` (Local)
Contains sensitive information:
- Database credentials
- API keys (OpenAI)
- Flask secret key
- Feature flags

### `requirements.txt`
Python package dependencies. Install with:
```bash
pip install -r requirements.txt
```

### `setup.py` & `pyproject.toml`
Package metadata and installation configuration for distribution.

### `.gitignore`
Specifies files not tracked by Git:
- Python cache files
- Environment files
- Database files
- Log files

## Running the Application

### Development
```bash
python run.py
```

### Production (Docker)
```bash
docker-compose up --build
```

### Testing
```bash
python -m pytest tests/ -v
python -m pytest tests/ --cov=src/
```

## Adding New Features

### Adding a New Service
1. Create `src/review_clustering/services/your_service.py`
2. Implement your logic
3. Add tests in `tests/test_your_service.py`
4. Import and integrate into `PipelineService`

### Adding a New API Endpoint
1. Add route in `src/review_clustering/main.py`
2. Create corresponding service method
3. Add test in `tests/test_api.py`

### Adding a New Database Model
1. Create model in `src/review_clustering/models/`
2. Extend existing model file or create new one
3. Update database initialization

## Best Practices

- Keep services focused and single-responsibility
- Write tests for all new functionality
- Use main.py for Flask routes only
- Keep business logic in services
- Use configuration for tuneable parameters
- Document complex algorithms
- Follow PEP 8 style guide

## Notes

- Database path defaults to `data/cluster_analysis.db`
- Upload folder: `uploads/` (16MB max)
- Logs stored in `logs/` directory
- All timestamps use UTC
- Configuration is environment-based for flexibility
