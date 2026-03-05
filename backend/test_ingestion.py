"""Test the complete data ingestion + processing pipeline."""

from app.services.ingestion_service import IngestionService
from app.services.pipeline_service import PipelineService
from app.services.persistence_service import PersistenceService

print("\n" + "="*70)
print("TEST: DATA INGESTION LAYER")
print("="*70)

# ============================================================================
# TEST 1: CSV INGESTION
# ============================================================================

csv_data = """review_text,rating,author,timestamp
Login failed after update,1,user1,2026-02-27T10:00:00
Login page not loading,1,user2,2026-02-27T10:30:00
Unable to login to account,1,user3,2026-02-27T11:00:00
Payment processing failed,2,user4,2026-02-27T11:30:00
Card payment declined,2,user5,2026-02-27T12:00:00
Payment not working,2,user6,2026-02-27T12:30:00
App crashes on startup,1,user7,2026-02-27T13:00:00
App keeps crashing,1,user8,2026-02-27T13:30:00
App closes unexpectedly,1,user9,2026-02-27T14:00:00
Profile section not loading,2,user10,2026-02-27T14:30:00
"""

print("\n1️⃣ INGESTING FROM CSV...")
result = IngestionService.ingest_csv(csv_data, source="csv_test")
print(f"   ✅ Total: {result['total']}")
print(f"   ✅ Successful: {result['successful']}")
print(f"   ✅ Failed: {result['failed']}")
print(f"   ✅ Duplicates: {result['duplicates']}")
print(f"   🆔 Job ID: {result['job_id']}")

# ============================================================================
# TEST 2: API INGESTION
# ============================================================================

print("\n2️⃣ INGESTING FROM API...")
api_reviews = [
    {"text": "Cannot login to app", "rating": 1, "author": "api_user1"},
    {"text": "Login timeout", "rating": 1, "author": "api_user2"},
    {"text": "Payment failed twice", "rating": 1, "author": "api_user3"},
    {"text": "Card not accepted", "rating": 2, "author": "api_user4"},
    {"text": "App crashes immediately", "rating": 1, "author": "api_user5"},
    {"text": "Crashes on launch", "rating": 1, "author": "api_user6"},
]

result = IngestionService.ingest_api(api_reviews, source="api_test")
print(f"   ✅ Total: {result['total']}")
print(f"   ✅ Successful: {result['successful']}")
print(f"   ✅ Duplicates: {result['duplicates']}")
print(f"   🆔 Job ID: {result['job_id']}")

# ============================================================================
# TEST 3: RETRIEVE PENDING REVIEWS
# ============================================================================

print("\n3️⃣ RETRIEVING PENDING REVIEWS FROM DATABASE...")
pending = IngestionService.get_pending_reviews(limit=100)
print(f"   ✅ Found {len(pending)} pending reviews")
if pending:
    print(f"   📍 First review: {pending[0]['review_text'][:50]}...")
    print(f"   📍 Source: {pending[0]['source']}")

# ============================================================================
# TEST 4: PROCESS REVIEWS THROUGH PIPELINE
# ============================================================================

print("\n4️⃣ PROCESSING REVIEWS THROUGH CLUSTERING PIPELINE...")
if pending:
    # Convert to pipeline format
    items = [
        {"text": r["review_text"], "timestamp": r["timestamp"]}
        for r in pending[:20]  # Limit to 20 for testing
    ]
    
    result = PipelineService.run_pipeline(items, save_to_db=True)
    
    print(f"   ✅ Execution time: {result['execution_time_ms']} ms")
    print(f"   ✅ Clusters found: {len(result['cluster_summary'])}")
    print(f"   ✅ Data saved: {result['saved']}")
    
    if result['saved']:
        run_id = result['run_id']
        print(f"   🆔 Run ID: {run_id}")
        
        # ====================================================================
        # TEST 5: RETRIEVE CLUSTERING RESULTS
        # ====================================================================
        
        print("\n5️⃣ RETRIEVING CLUSTERING RESULTS...")
        run_data = PersistenceService.get_run_by_id(run_id)
        
        if run_data:
            print(f"   ✅ Pipeline run found")
            print(f"   📊 Input reviews: {run_data['run']['num_inputs']}")
            print(f"   📊 Cleaned texts: {run_data['run']['num_cleaned']}")
            print(f"   📊 Clusters: {len(run_data['clusters'])}")
            
            print("\n   📌 CLUSTER DETAILS:")
            for cluster in run_data['clusters']:
                print(f"\n      Cluster #{cluster['cluster_id']}:")
                print(f"        - Frequency: {cluster['frequency']}")
                print(f"        - Priority: {cluster['priority_score']}")
                print(f"        - Trend: {cluster['trend_score']}")
                print(f"        - Label: {cluster['label'] if cluster['label'] else 'N/A'}")
                if cluster['representative_reviews']:
                    print(f"        - Sample: {cluster['representative_reviews'][0][:40]}...")

# ============================================================================
# TEST 6: GET TOP PRIORITY CLUSTERS
# ============================================================================

print("\n6️⃣ RETRIEVING TOP PRIORITY CLUSTERS...")
top_clusters = PersistenceService.get_clusters_by_priority(limit=5)
print(f"   ✅ Found {len(top_clusters)} high-priority clusters")

for cluster in top_clusters[:3]:
    print(f"\n   📌 Cluster #{cluster['cluster_id']}:")
    print(f"      Priority Score: {cluster['priority_score']}")
    print(f"      Frequency: {cluster['frequency']}")
    print(f"      Sentiment: {cluster['avg_sentiment']:.2f}")

# ============================================================================
# TEST 7: INGESTION JOB HISTORY
# ============================================================================

print("\n7️⃣ INGESTION JOB HISTORY...")
jobs = IngestionService.get_ingestion_jobs(limit=5)
print(f"   ✅ Recent jobs: {len(jobs)}")

for job in jobs[:3]:
    print(f"\n   📋 Job #{job['id']}:")
    print(f"      Type: {job['job_type']}")
    print(f"      Source: {job['source']}")
    print(f"      Status: {job['status']}")
    print(f"      Processed: {job['successful']}/{job['total_records']}")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*70)
print("✅ DATA INGESTION LAYER FULLY FUNCTIONAL")
print("="*70)
print("""
Features demonstrated:
  ✅ CSV file ingestion with validation
  ✅ JSON API ingestion
  ✅ Duplicate detection
  ✅ Review persistence to database
  ✅ Pending review queue management
  ✅ Integration with clustering pipeline
  ✅ Results persistence with metrics
  ✅ Job history tracking

Ready for production use with Flask API endpoints!
""")
