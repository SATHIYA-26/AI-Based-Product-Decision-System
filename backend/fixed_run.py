#!/usr/bin/env python
"""
Fixed Flask app runner with delayed model loading.
"""

import sys
import os

# Add the src directory to sys.path for imports
backend_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(backend_dir, 'src')
sys.path.insert(0, src_dir)

print("Starting backend with delayed loading...")

try:
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    from werkzeug.utils import secure_filename
    from apscheduler.schedulers.background import BackgroundScheduler
    import json
    
    # Import services that don't load heavy models
    from review_clustering.services.ingestion_service import IngestionService
    from review_clustering.services.preprocessing_service import PreprocessingService  
    from review_clustering.services.sentiment_service import SentimentService
    from review_clustering.services.priority_service import PriorityService
    from review_clustering.services.sampling_service import SamplingService
    from review_clustering.services.persistence_service import PersistenceService
    from review_clustering.services.trend_service import TrendService
    
    print("✅ Basic imports successful!")
    
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), '..', 'uploads')
    
    CORS(app, origins=['http://localhost:3000', 'http://127.0.0.1:3000'])
    
    os.makedirs(app.config['UPLOAD_FOLDER'], mode=0o755, exist_ok=True)
    
    scheduler = BackgroundScheduler()
    
    # Health endpoint
    @app.route('/health')
    def health():
        return {"status": "ok"}
    
    # Customer problems endpoint with delayed loading
    @app.route('/customer-problems', methods=['GET'])
    def get_customer_problems():
        try:
            limit = request.args.get('limit', 10, type=int)
            
            # Get most recent run
            recent_runs = PersistenceService.list_recent_runs(limit=1)
            
            if not recent_runs:
                return jsonify({
                    "problems": [],
                    "total_problems": 0,
                    "last_updated": "2024-03-06T10:18:00Z"
                }), 200
            
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
            seen_labels = set()
            
            for cluster in clusters:
                label = cluster.get("label", "Unknown Issue").strip()
                
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
            
            problems.sort(key=lambda x: x.get("priority_score", 0), reverse=True)
            
            return jsonify({
                "problems": problems[:limit],
                "total_problems": len(problems),
                "last_updated": "2024-03-06T10:18:00Z"
            }), 200
            
        except Exception as e:
            return jsonify({"error": f"Failed to get customer problems: {str(e)}"}), 500
    
    def get_priority_label(priority_score):
        if priority_score >= 0.8:
            return "High"
        elif priority_score >= 0.5:
            return "Medium"
        else:
            return "Low"
    
    # Info endpoint
    @app.route('/info')
    def info():
        return jsonify({
            "service": "Review Clustering Pipeline",
            "version": "2.0.0",
            "endpoints": {
                "health": "GET /health - Check API status",
                "customer-problems": "GET /customer-problems - Get customer problems for dashboard"
            }
        })
    
    print("✅ App created successfully!")
    
    if __name__ == '__main__':
        print("Starting Review Clustering Pipeline API...")
        print("Available at http://localhost:5000")
        print("API docs at http://localhost:5000/info")
        app.run(debug=True, host='0.0.0.0', port=5000)
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
