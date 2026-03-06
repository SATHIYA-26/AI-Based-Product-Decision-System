"""
Configuration module for Review Clustering System.

Handles environment variables, database settings, and application configuration.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# ============================================
# DATABASE CONFIGURATION
# ============================================
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///data/cluster_analysis.db"
)

# ============================================
# OPENAI CONFIGURATION
# ============================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ============================================
# FLASK CONFIGURATION
# ============================================
FLASK_ENV = os.getenv("FLASK_ENV", "development")
FLASK_DEBUG = FLASK_ENV == "development"
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")

# File upload settings
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, "uploads")

# ============================================
# LOGGING CONFIGURATION
# ============================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")

# ============================================
# SCHEDULER CONFIGURATION
# ============================================
SCHEDULER_INTERVAL = int(os.getenv("SCHEDULER_INTERVAL", "1"))  # hours

# ============================================
# TEXT PROCESSING CONFIGURATION
# ============================================
SPACY_MODEL = os.getenv("SPACY_MODEL", "en_core_web_sm")
MIN_REVIEW_LENGTH = int(os.getenv("MIN_REVIEW_LENGTH", "10"))

# ============================================
# CLUSTERING CONFIGURATION
# ============================================
CLUSTER_MIN_SIZE = int(os.getenv("CLUSTER_MIN_SIZE", "5"))
CLUSTER_MIN_SAMPLES = int(os.getenv("CLUSTER_MIN_SAMPLES", "3"))

# ============================================
# API CONFIGURATION
# ============================================
API_ENDPOINT = os.getenv("API_ENDPOINT", "")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))

# ============================================
# EMAIL CONFIGURATION (Optional)
# ============================================
MAIL_SERVER = os.getenv("MAIL_SERVER", "")
MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
MAIL_FROM = os.getenv("MAIL_FROM", "noreply@example.com")

# ============================================
# MONITORING & ERROR TRACKING (Optional)
# ============================================
SENTRY_DSN = os.getenv("SENTRY_DSN", "")

# ============================================
# CORS CONFIGURATION
# ============================================
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5000").split(",")

# ============================================
# FEATURE FLAGS
# ============================================
ENABLE_TREND_ANALYSIS = os.getenv("ENABLE_TREND_ANALYSIS", "true").lower() == "true"
ENABLE_LLM_SUMMARIES = os.getenv("ENABLE_LLM_SUMMARIES", "true").lower() == "true"
ENABLE_AUTO_SCHEDULING = os.getenv("ENABLE_AUTO_SCHEDULING", "true").lower() == "true"


def ensure_directories():
    """Ensure all required directories exist."""
    directories = [
        os.path.dirname(LOG_FILE),
        UPLOAD_FOLDER,
        os.path.join(PROJECT_ROOT, "data"),
    ]
    
    for directory in directories:
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)


# Create directories on import
ensure_directories()
