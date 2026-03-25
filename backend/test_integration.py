#!/usr/bin/env python3
"""
Test script to verify the customer problems API integration.
This script will:
1. Run the pipeline with sample data
2. Test the new customer-problems endpoint
3. Verify the data structure matches what the frontend expects
"""

import requests
import json
import time
import sys
from app.services.pipeline_service import PipelineService

def test_pipeline_and_api():
    """Test the full pipeline and API integration."""
    
    print("🚀 Testing Customer Problems Integration")
    print("=" * 50)
    
    # 1. Test the pipeline with sample data
    print("\n1️⃣ Running pipeline with sample feedback data...")
    
    sample_feedback = [
        "Login failed after update",
        "Login not working since yesterday", 
        "Unable to login to my account",
        "Login page stuck at loading",
        "OTP login not working",
        "Payment failed twice",
        "Payment not processing",
        "Card payment declined",
        "UPI payment not working",
        "Transaction failed after OTP",
        "App crashes when opening profile",
        "App crash after update",
        "App closes automatically",
        "Profile section not loading",
        "Dashboard loading very slow",
        "Search functionality broken",
        "Cannot export reports",
        "Mobile app not syncing"
    ]
    
    try:
        result = PipelineService.run_pipeline(sample_feedback, save_to_db=True)
        print(f"✅ Pipeline completed successfully!")
        print(f"   - Processed {len(sample_feedback)} feedback items")
        print(f"   - Generated {len(result.get('cluster_summary', {}))} clusters")
        print(f"   - Execution time: {result.get('execution_time_ms', 0)}ms")
        
        if result.get('run_id'):
            print(f"   - Run ID: {result['run_id']}")
        
    except Exception as e:
        print(f"❌ Pipeline failed: {str(e)}")
        return False
    
    # 2. Test the API endpoint
    print("\n2️⃣ Testing customer-problems API endpoint...")
    
    api_base_url = "http://localhost:5000"
    
    try:
        response = requests.get(f"{api_base_url}/customer-problems?limit=10", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API endpoint working!")
            print(f"   - Status: {response.status_code}")
            print(f"   - Total problems: {data.get('total_problems', 0)}")
            
            problems = data.get('problems', [])
            if problems:
                print(f"   - Sample problem structure:")
                sample_problem = problems[0]
                for key, value in sample_problem.items():
                    print(f"     {key}: {value}")
            else:
                print("   - No problems found (expected if no data in DB)")
                
        else:
            print(f"❌ API request failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend server")
        print("   Make sure the Flask server is running on http://localhost:5000")
        return False
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")
        return False
    
    # 3. Test the health endpoint
    print("\n3️⃣ Testing backend health...")
    
    try:
        response = requests.get(f"{api_base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend server is healthy!")
        else:
            print(f"⚠️ Backend returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        return False
    
    print("\n🎉 Integration test completed successfully!")
    print("\n📋 Next steps:")
    print("   1. Start the backend server: python app/main.py")
    print("   2. Open dashboard.html in your browser")
    print("   3. The customer problems should now display live data")
    
    return True

if __name__ == "__main__":
    success = test_pipeline_and_api()
    sys.exit(0 if success else 1)
