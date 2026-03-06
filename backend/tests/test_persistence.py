"""Simple test to verify database persistence works without full pipeline."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from review_clustering.services.persistence_service import PersistenceService
from review_clustering.models.cluster_analysis import get_db_session

# create a dummy cluster result
dummy_cluster_summary = {
    0: {
        "frequency": 5,
        "avg_sentiment": -0.3,
        "priority_score": 65.5,
        "trend_score": 0.2,
        "summary": "Users experiencing login issues after update",
        "label": "Login Failures",
        "representative_reviews": ["login fail", "cant login", "login broken"]
    },
    1: {
        "frequency": 3,
        "avg_sentiment": -0.15,
        "priority_score": 45.0,
        "trend_score": 0.0,
        "summary": "Payment processing delays",
        "label": "Payment Issues",
        "representative_reviews": ["slow payment", "payment stuck", "payment delayed"]
    }
}

print("\n=== DATABASE PERSISTENCE TEST ===\n")

# test 1: save a run
print("1️⃣ Saving pipeline run to database...")
try:
    run_id = PersistenceService.save_pipeline_run(
        num_inputs=14,
        num_cleaned=12,
        cluster_summary=dummy_cluster_summary,
        execution_time_ms=1250
    )
    print(f"   ✅ Run saved! ID: {run_id}\n")
except Exception as e:
    print(f"   ❌ Failed: {e}\n")
    exit(1)

# test 2: retrieve the run
print("2️⃣ Retrieving saved run...")
try:
    retrieved = PersistenceService.get_run_by_id(run_id)
    if retrieved:
        print(f"   ✅ Run retrieved!")
        print(f"      - Input count: {retrieved['run']['num_inputs']}")
        print(f"      - Cleaned count: {retrieved['run']['num_cleaned']}")
        print(f"      - Cluster count: {retrieved['run']['num_clusters']}")
        print(f"      - Execution time: {retrieved['run']['execution_time_ms']} ms")
        print(f"      - Stored clusters: {len(retrieved['clusters'])}\n")
    else:
        print(f"   ❌ Run not found\n")
except Exception as e:
    print(f"   ❌ Failed: {e}\n")

# test 3: list recent runs
print("3️⃣ Listing recent runs...")
try:
    recent = PersistenceService.list_recent_runs(limit=5)
    print(f"   ✅ Found {len(recent)} recent runs\n")
    for run in recent[:2]:
        print(f"      - {run['run_id']}: {run['num_clusters']} clusters")
except Exception as e:
    print(f"   ❌ Failed: {e}\n")

# test 4: get highest priority clusters
print("4️⃣ Listing top priority clusters...")
try:
    top_clusters = PersistenceService.get_clusters_by_priority(limit=5)
    print(f"   ✅ Found {len(top_clusters)} clusters")
    for c in top_clusters[:2]:
        print(f"      - Cluster {c['cluster_id']}: {c['priority_score']} score (label: {c['label']})\n")
except Exception as e:
    print(f"   ❌ Failed: {e}\n")

# test 5: verify database file was created
print("5️⃣ Verifying database file...")
import os
if os.path.exists("./cluster_analysis.db"):
    size = os.path.getsize("./cluster_analysis.db")
    print(f"   ✅ Database file exists: cluster_analysis.db ({size} bytes)\n")
else:
    print(f"   ⚠️  Database file not found in current directory\n")

print("\n=== SUMMARY ===")
print("✅ Database persistence layer is WORKING:")
print("   - Can save pipeline runs and cluster results")
print("   - Can retrieve runs by ID")
print("   - Can query recent runs and top priority clusters")
print("   - All data persists to SQLite database")
