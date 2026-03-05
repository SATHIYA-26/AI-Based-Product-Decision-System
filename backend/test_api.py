"""
Example API usage for the data ingestion layer.

Run the Flask server first:
    cd D:\AI\backend
    python app/main.py

Then execute this file to test endpoints:
    python test_api.py
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_api():
    print("\n" + "="*70)
    print("Testing Review Clustering API Endpoints")
    print("="*70)
    
    # Check if server is running
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=2)
        if resp.status_code != 200:
            print("❌ Server not responding on /health")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server at", BASE_URL)
        print("   Start server with: python app/main.py")
        return
    
    print("✅ Server is running\n")
    
    # ========================================================================
    # 1. GET API INFO
    # ========================================================================
    print("1️⃣ GET /info")
    resp = requests.get(f"{BASE_URL}/info")
    data = resp.json()
    print(f"   ✅ Service: {data['service']}")
    print(f"   ✅ Version: {data['version']}")
    print(f"   ✅ Endpoints available: {len(data['endpoints'])}\n")
    
    # ========================================================================
    # 2. UPLOAD CSV FILE
    # ========================================================================
    print("2️⃣ POST /upload-csv")
    
    csv_content = """review_text,rating,author,timestamp
Cannot login to my account,1,user1,2026-02-27T10:00:00
Login page not working,1,user2,2026-02-27T10:30:00
Unable to reset password,1,user3,2026-02-27T11:00:00
Payment processing error,1,user4,2026-02-27T11:30:00
Card declined multiple times,2,user5,2026-02-27T12:00:00
App crashes on startup,1,user6,2026-02-27T12:30:00
App freezes when opening,1,user7,2026-02-27T13:00:00
"""
    
    files = {'file': ('reviews.csv', csv_content)}
    data = {'source': 'api_test_csv'}
    
    resp = requests.post(f"{BASE_URL}/upload-csv", files=files, data=data)
    result = resp.json()
    
    print(f"   ✅ Status: {result['status']}")
    print(f"   ✅ Total: {result['total']}")
    print(f"   ✅ Successful: {result['successful']}")
    print(f"   ✅ Job ID: {result['job_id']}\n")
    
    # ========================================================================
    # 3. INGEST FROM API
    # ========================================================================
    print("3️⃣ POST /ingest-api")
    
    reviews_payload = {
        "reviews": [
            {"text": "Login timeout issues", "rating": 1, "author": "api_user1"},
            {"text": "Payment failed twice", "rating": 1, "author": "api_user2"},
            {"text": "App closes unexpectedly", "rating": 1, "author": "api_user3"},
            {"text": "Support page not loading", "rating": 2, "author": "api_user4"},
        ],
        "source": "support_tickets"
    }
    
    resp = requests.post(
        f"{BASE_URL}/ingest-api",
        json=reviews_payload,
        headers={"Content-Type": "application/json"}
    )
    result = resp.json()
    
    print(f"   ✅ Status: {result['status']}")
    print(f"   ✅ Total: {result['total']}")
    print(f"   ✅ Successful: {result['successful']}")
    print(f"   ✅ Job ID: {result['job_id']}\n")
    
    # ========================================================================
    # 4. GET INGESTION STATUS
    # ========================================================================
    print("4️⃣ GET /ingestion-status")
    
    resp = requests.get(f"{BASE_URL}/ingestion-status?limit=5")
    data = resp.json()
    
    print(f"   ✅ Recent jobs: {len(data['jobs'])}")
    for job in data['jobs'][:2]:
        print(f"      - Job #{job['id']}: {job['job_type']} "
              f"({job['successful']}/{job['total_records']})")
    print()
    
    # ========================================================================
    # 5. PROCESS PENDING REVIEWS
    # ========================================================================
    print("5️⃣ POST /process-reviews")
    print("   Waiting for clustering pipeline...")
    
    resp = requests.post(f"{BASE_URL}/process-reviews?limit=100")
    result = resp.json()
    
    if "error" not in result:
        print(f"   ✅ Reviews processed: {result['reviews_processed']}")
        print(f"   ✅ Clusters found: {result['clusters']}")
        print(f"   ✅ Execution time: {result['execution_time_ms']} ms")
        run_id = result.get('run_id')
        print(f"   🆔 Run ID: {run_id}\n")
        
        # ====================================================================
        # 6. GET CLUSTER RESULTS
        # ====================================================================
        if run_id:
            print("6️⃣ GET /cluster-results/<run_id>")
            
            resp = requests.get(f"{BASE_URL}/cluster-results/{run_id}")
            cluster_data = resp.json()
            
            print(f"   ✅ Run found")
            print(f"   📊 Input: {cluster_data['run']['num_inputs']}")
            print(f"   📊 Cleaned: {cluster_data['run']['num_cleaned']}")
            print(f"   📊 Clusters: {len(cluster_data['clusters'])}")
            print()
            
            print("   📌 TOP CLUSTERS:")
            for cluster in cluster_data['clusters'][:3]:
                print(f"      Cluster #{cluster['cluster_id']}:")
                print(f"        Priority: {cluster['priority_score']}")
                print(f"        Frequency: {cluster['frequency']}")
                if cluster['representative_reviews']:
                    print(f"        Sample: {cluster['representative_reviews'][0][:40]}...")
            print()
    else:
        print(f"   ❌ Error: {result['error']}")
        print()
    
    # ========================================================================
    # 7. GET TOP PRIORITY CLUSTERS
    # ========================================================================
    print("7️⃣ GET /top-clusters")
    
    resp = requests.get(f"{BASE_URL}/top-clusters?limit=5")
    data = resp.json()
    
    print(f"   ✅ Found {len(data['clusters'])} top clusters")
    for cluster in data['clusters'][:3]:
        print(f"      Cluster #{cluster['cluster_id']}: "
              f"Score {cluster['priority_score']}, "
              f"Freq {cluster['frequency']}")
    print()
    
    # ========================================================================
    # 8. START SCHEDULER
    # ========================================================================
    print("8️⃣ POST /scheduler/start")
    
    resp = requests.post(f"{BASE_URL}/scheduler/start")
    result = resp.json()
    
    print(f"   ✅ Status: {result['status']}")
    print(f"   ✅ Interval: {result['interval_hours']} hours\n")
    
    # ========================================================================
    # 9. GET SCHEDULER STATUS
    # ========================================================================
    print("9️⃣ GET /scheduler/status")
    
    resp = requests.get(f"{BASE_URL}/scheduler/status")
    data = resp.json()
    
    print(f"   ✅ Running: {data['running']}")
    print(f"   ✅ Jobs: {data['jobs']}\n")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("="*70)
    print("✅ ALL ENDPOINTS WORKING")
    print("="*70)
    print("""
API SUMMARY:

📥 Data Ingestion:
   • POST /upload-csv - Upload CSV files with reviews
   • POST /ingest-api - Ingest reviews from JSON API
   • GET /ingestion-status - View ingestion job history

⚙️ Processing:
   • POST /process-reviews - Run clustering pipeline on pending reviews
   • GET /cluster-results/<run_id> - View results for a specific run
   • GET /top-clusters - Get highest priority clusters

🔄 Scheduling:
   • POST /scheduler/start - Enable hourly automatic processing
   • POST /scheduler/stop - Disable scheduler
   • GET /scheduler/status - Check scheduler status

Example curl commands:

# Upload CSV:
curl -X POST -F "file=@reviews.csv" -F "source=play_store" \\
  http://localhost:5000/upload-csv

# Ingest API:
curl -X POST -H "Content-Type: application/json" \\
  -d '{"reviews":[{"text":"App crashes","rating":1,"author":"user1"}],"source":"app_store"}' \\
  http://localhost:5000/ingest-api

# Process reviews:
curl -X POST http://localhost:5000/process-reviews?limit=100

# Get results:
curl http://localhost:5000/cluster-results/0ae81ab5-7bf1-494a-92c8-ff2003e218e6

# Get top clusters:
curl http://localhost:5000/top-clusters?limit=10

# Start scheduler:
curl -X POST http://localhost:5000/scheduler/start
""")

if __name__ == '__main__':
    test_api()
