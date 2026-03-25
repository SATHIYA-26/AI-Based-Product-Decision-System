#!/usr/bin/env python
"""
Step-by-step import tester for main.py
"""

import sys
import os

# Add the src directory to sys.path for imports
backend_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(backend_dir, 'src')
sys.path.insert(0, src_dir)

print("Testing imports step by step...")

# Test basic imports
try:
    print("1. Testing Flask...")
    from flask import Flask, request, jsonify
    print("   ✅ Flask OK")
except Exception as e:
    print(f"   ❌ Flask failed: {e}")
    exit(1)

try:
    print("2. Testing flask_cors...")
    from flask_cors import CORS
    print("   ✅ flask_cors OK")
except Exception as e:
    print(f"   ❌ flask_cors failed: {e}")
    exit(1)

try:
    print("3. Testing werkzeug...")
    from werkzeug.utils import secure_filename
    print("   ✅ werkzeug OK")
except Exception as e:
    print(f"   ❌ werkzeug failed: {e}")
    exit(1)

try:
    print("4. Testing apscheduler...")
    from apscheduler.schedulers.background import BackgroundScheduler
    print("   ✅ apscheduler OK")
except Exception as e:
    print(f"   ❌ apscheduler failed: {e}")
    exit(1)

# Test service imports
try:
    print("5. Testing ingestion_service...")
    from review_clustering.services.ingestion_service import IngestionService
    print("   ✅ ingestion_service OK")
except Exception as e:
    print(f"   ❌ ingestion_service failed: {e}")
    exit(1)

try:
    print("6. Testing pipeline_service...")
    from review_clustering.services.pipeline_service import PipelineService
    print("   ✅ pipeline_service OK")
except Exception as e:
    print(f"   ❌ pipeline_service failed: {e}")
    exit(1)

try:
    print("7. Testing sync_service...")
    from review_clustering.services.sync_service import get_sync_service, ReviewSyncService
    print("   ✅ sync_service OK")
except Exception as e:
    print(f"   ❌ sync_service failed: {e}")
    exit(1)

try:
    print("8. Testing scheduler_service...")
    from review_clustering.services.scheduler_service import (
        get_scheduler_service, AutomatedSchedulerService, start_automated_sync
    )
    print("   ✅ scheduler_service OK")
except Exception as e:
    print(f"   ❌ scheduler_service failed: {e}")
    exit(1)

try:
    print("9. Testing connectors...")
    from review_clustering.connectors import (
        ConnectorConfig, ReviewData, GooglePlayConnector, AppStoreConnector, GenericAPIConnector
    )
    print("   ✅ connectors OK")
except Exception as e:
    print(f"   ❌ connectors failed: {e}")
    exit(1)

print("\n✅ All imports successful! Creating app...")

# Create app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), '..', 'uploads')

CORS(app, origins=['http://localhost:3000', 'http://127.0.0.1:3000'])

os.makedirs(app.config['UPLOAD_FOLDER'], mode=0o755, exist_ok=True)

scheduler = BackgroundScheduler()

print("✅ App created successfully!")

if __name__ == '__main__':
    print("Starting server...")
    print("Available at http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
