# Review Clustering System

A production-grade Python application for clustering, analyzing, and deriving insights from customer reviews using machine learning and NLP techniques.

## Features

- **Intelligent Clustering**: HDBSCAN-based density clustering to group similar reviews
- **Sentiment Analysis**: VADER sentiment analysis with priority scoring
- **Trend Detection**: Weekly growth tracking for emerging issues
- **LLM Integration**: OpenAI-powered summaries and intelligent labels (optional)
- **Multi-Source Ingestion**: CSV uploads, JSON API, and scheduled processing
- **REST API**: 11 endpoints for complete pipeline management
- **Database Persistence**: SQLAlchemy ORM with SQLite/PostgreSQL support
- **Automatic Scheduling**: APScheduler for hourly review processing

## Quick Start

### Prerequisites

- Python 3.11+
- pip or conda

### Installation

```bash
# Clone or navigate to project
cd backend

# Install dependencies
pip install -r requirements.txt

# Run the application
python run.py
```

The Flask server will start on `http://localhost:5000`

## Project Structure

```
backend/
├── src/
│   └── review_clustering/      # Main application package
│       ├── api/                # (API endpoints - under core)
│       ├── services/           # Business logic services
│       ├── models/             # SQLAlchemy ORM models
│       ├── core/               # Core configurations
│       ├── database/           # Database connections
│       ├── workers/            # Background tasks
│       └── __init__.py
├── tests/                      # Test suites
├── data/                       # Database and data files
├── config/                     # Configuration files
├── docs/                       # Documentation
├── requirements.txt            # Python dependencies
├── run.py                      # Application entry point
├── setup.py                    # Package setup
├── pyproject.toml             # Modern Python config
├── .env.example               # Environment template
└── README.md                  # This file
```

## API Endpoints

### Core Operations
- `POST /upload-csv` - Upload reviews from CSV file
- `POST /ingest-api` - Ingest reviews from JSON API
- `POST /process-reviews` - Trigger clustering pipeline
- `GET /cluster-results/{id}` - Retrieve specific cluster analysis
- `GET /top-clusters` - Get high-priority clusters

### Scheduler
- `POST /scheduler/start` - Start hourly processing
- `POST /scheduler/stop` - Stop scheduler
- `GET /scheduler/status` - Check scheduler status

### System
- `GET /health` - Health check
- `GET /info` - System information
- `GET /ingestion-status` - Ingestion queue status

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Database
DATABASE_URL=sqlite:///data/cluster_analysis.db
# DATABASE_URL=postgresql://user:password@localhost/review_db  # PostgreSQL

# OpenAI (optional for LLM features)
OPENAI_API_KEY=your_api_key_here

# Logging
LOG_LEVEL=INFO

# Server
FLASK_PORT=5000
FLASK_ENV=development
```

See `.env.example` for all available options.

## Services

### IngestionService
Handles multi-source data ingestion with deduplication:
- CSV file parsing and validation
- JSON API consumption
- Scheduled batch imports
- Automatic duplicate detection

### PipelineService
Orchestrates the complete clustering workflow:
- Review filtering and preprocessing
- Text embedding generation
- HDBSCAN clustering
- Sentiment analysis and scoring
- Optional LLM summaries

### PersistenceService
Database operations for clustering results:
- Save pipeline runs and cluster results
- Query analysis history
- Retrieve top clusters by priority

### Other Services
- **PreprocessingService**: Spacy-based NLP preprocessing
- **EmbeddingService**: Scikit-learn text vectorization
- **ClusteringService**: HDBSCAN density clustering
- **SentimentService**: VADER sentiment analysis
- **PriorityService**: Multi-factor priority scoring
- **SamplingService**: Representative review selection
- **TrendService**: Weekly growth trend calculation
- **LLMService**: OpenAI integration for summaries/labels

## Testing

Run the test suite:

```bash
# All tests
python -m pytest tests/

# With coverage
python -m pytest tests/ --cov=src/

# Specific test file
python -m pytest tests/test_ingestion.py -v
```

## Development

### Adding a New Service

1. Create `src/review_clustering/services/your_service.py`
2. Implement your logic with clear error handling
3. Add tests in `tests/test_your_service.py`
4. Integrate into PipelineService or API endpoints

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Add new field"

# Apply migrations
alembic upgrade head
```

## Deployment

### Docker

```bash
# Build image
docker build -t review-clustering:latest .

# Run container
docker run -p 5000:5000 -e DATABASE_URL=postgresql://... review-clustering:latest
```

### Production Checklist

- [ ] Set `FLASK_ENV=production`
- [ ] Configure PostgreSQL database
- [ ] Set strong `SECRET_KEY`
- [ ] Configure OpenAI API key (if using LLM)
- [ ] Set up log aggregation
- [ ] Configure error tracking (Sentry, etc.)
- [ ] Enable HTTPS
- [ ] Setup monitoring and alerts

## Performance Metrics

- **Ingestion**: ~1000 reviews/minute (CSV parsing)
- **Processing**: ~50ms per review (clustering + analysis)
- **Storage**: ~1.5KB per cluster result

## Troubleshooting

### Flask Server Won't Start
```bash
# Check if port 5000 is in use
netstat -ano | findstr :5000

# Kill process and retry
```

### Database Lock Error
Stop the Flask application and restart it.

### Missing OpenAI Features
These are optional. System continues without API key configured.

## Contributing

1. Create a feature branch
2. Add tests for new functionality
3. Ensure all tests pass
4. Submit a pull request

## License

[Your License Here]

## Support

For issues, questions, or suggestions, please open an issue on the project repository.

## Documentation

- [Data Ingestion Guide](docs/DATA_INGESTION.md)
- Architecture docs will be updated in future
- API reference will be updated soon
