# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-03-01

### Added
- Initial release of Review Clustering System
- Multi-source data ingestion (CSV, JSON API, scheduled)
- HDBSCAN-based clustering algorithm
- Sentiment analysis with VADER
- Priority scoring based on frequency and sentiment
- Weekly trend detection for emerging issues
- LLM integration for summaries and labels (OpenAI)
- SQLAlchemy ORM with SQLite/PostgreSQL support
- REST API with 11 endpoints
- APScheduler for hourly automatic processing
- Comprehensive test suite
- Docker support for containerized deployment
- Professional project structure with proper packaging

### Features
- **Core Pipeline**: Filter → Preprocess → Embed → Cluster → Analyze
- **Multi-Source Ingestion**: Upload CSV, parse JSON API, schedule batch jobs
- **Smart Deduplication**: Detect duplicate reviews across sources
- **Trend Analysis**: Track weekly growth of clusters
- **Priority Scoring**: Multi-factor scoring for issue prioritization
- **RESTful API**: Full endpoint coverage for all major operations
- **Automatic Scheduling**: Hourly processing with APScheduler
- **Database Persistence**: Full audit trail and result history

## [Unreleased]

### Planned
- Celery task queue integration for distributed processing
- Email alerts for high-priority clusters
- Web dashboard UI (React/Vue)
- Advanced analytics and reporting
- Webhooks for external systems
- Rate limiting and authentication
- Multi-tenant support
- Custom wordlists for domain-specific preprocessing
- A/B testing framework for algorithm improvements
- Export to various formats (PDF, Excel, JSON)
- Elasticsearch integration for full-text search
