#!/usr/bin/env python
"""
Minimal Flask app runner for testing.
"""

import sys
import os

# Add the src directory to sys.path for imports
backend_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(backend_dir, 'src')
sys.path.insert(0, src_dir)

print("Starting minimal test...")

try:
    from flask import Flask
    from flask_cors import CORS
    
    # Create minimal app
    app = Flask(__name__)
    CORS(app, origins=['http://localhost:3000', 'http://127.0.0.1:3000'])
    
    @app.route('/health')
    def health():
        return {"status": "ok"}
    
    @app.route('/customer-problems')
    def customer_problems():
        return {"problems": [], "total_problems": 0}
    
    print("✅ Minimal app created successfully!")
    
    if __name__ == '__main__':
        print("Starting minimal Flask server...")
        print("Available at http://localhost:5000")
        app.run(debug=True, host='0.0.0.0', port=5000)
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
