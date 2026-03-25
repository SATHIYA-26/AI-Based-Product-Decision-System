#!/usr/bin/env python
"""
Flask app runner - properly sets up Python path and runs the server.

Usage:
    cd D:\\AI\\backend
    python run.py
"""

import sys
import os

# Add the src directory to sys.path for imports
backend_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(backend_dir, 'src')
sys.path.insert(0, src_dir)

# Also set PYTHONPATH for Flask's reloader
os.environ['PYTHONPATH'] = src_dir + os.pathsep + os.environ.get('PYTHONPATH', '')

from review_clustering.main import app

if __name__ == '__main__':
    print("Starting Review Clustering Pipeline API...")
    print("Available at http://localhost:5000")
    print("API docs at http://localhost:5000/info")
    app.run(debug=True, host='0.0.0.0', port=5000)

