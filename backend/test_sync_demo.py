"""Full end-to-end demo of the Automated Review Sync System."""

import requests
import json
import sys

BASE = 'http://localhost:5002'

passed = 0
failed = 0


def pp(label, resp, expect_success=True):
    global passed, failed
    print(f'\n{label}')
    print(f'  HTTP {resp.status_code}')
    data = resp.json()
    print(f'  {json.dumps(data, indent=2)[:600]}')
    
    # Check for success
    ok = resp.status_code < 400
    if expect_success and not ok:
        print(f'  *** FAILED ***')
        failed += 1
    else:
        passed += 1
    return data


print('=' * 70)
print('  AUTOMATED REVIEW SYNC SYSTEM - COMPLETE FLOW DEMO')
print('  (Google Play + Generic API)')
print('=' * 70)

# STEP 1: Health
r = requests.get(f'{BASE}/health')
pp('STEP 1: Health Check', r)

# STEP 2: Register Google Play Connector (mock data)
r = requests.post(f'{BASE}/connectors', json={
    'name': 'spotify_gplay',
    'source_type': 'google_play',
    'app_id': 'com.spotify.music',
    'fetch_limit': 5,
    'fetch_interval_minutes': 30
})
pp('STEP 2: Register Google Play Connector', r)

# STEP 3: Register Generic API Connector
r = requests.post(f'{BASE}/connectors', json={
    'name': 'internal_reviews',
    'source_type': 'api',
    'api_endpoint': 'https://jsonplaceholder.typicode.com/posts',
    'auth_type': 'none',
    'fetch_limit': 5,
    'extra_config': {
        'field_mapping': {
            'text': 'body',
            'rating': 'id',
            'author': 'userId',
            'source_id': 'id'
        },
        'response_path': ''
    }
})
pp('STEP 3: Register Generic API Connector', r)

# STEP 4: List Connectors
r = requests.get(f'{BASE}/connectors')
pp('STEP 4: List All Connectors', r)

# STEP 5: Test Google Play Connection
r = requests.post(f'{BASE}/connectors/spotify_gplay/test')
pp('STEP 5: Test Google Play Connection', r)

# STEP 6: Test Generic API Connection
r = requests.post(f'{BASE}/connectors/internal_reviews/test')
pp('STEP 6: Test Generic API Connection', r)

# STEP 7: Sync Google Play (mock reviews)
r = requests.post(f'{BASE}/sync/spotify_gplay?trigger_pipeline=false')
d = pp('STEP 7: Sync Google Play (mock reviews)', r)
if d.get('success'):
    print(f'  >>> Fetched {d["reviews_fetched"]} reviews!')

# STEP 8: Sync Generic API
r = requests.post(f'{BASE}/sync/internal_reviews?trigger_pipeline=false')
d = pp('STEP 8: Sync Generic API', r)
if d.get('success'):
    print(f'  >>> Fetched {d["reviews_fetched"]} reviews!')

# STEP 9: Sync History
r = requests.get(f'{BASE}/sync/history?limit=5')
pp('STEP 9: Sync History', r)

# STEP 10: Sync Stats
r = requests.get(f'{BASE}/sync/stats')
pp('STEP 10: Sync Statistics', r)

# STEP 11: Scheduler Status (before start)
r = requests.get(f'{BASE}/scheduler/sync/status')
pp('STEP 11: Scheduler Status (before start)', r)

# STEP 12: Add Scheduled Job
r = requests.post(f'{BASE}/scheduler/sync/jobs', json={
    'connector_name': 'spotify_gplay',
    'interval_minutes': 30
})
pp('STEP 12: Add Scheduled Sync Job', r)

# STEP 13: Start Scheduler
r = requests.post(f'{BASE}/scheduler/sync/start')
pp('STEP 13: Start Scheduler', r)

# STEP 14: List Scheduled Jobs
r = requests.get(f'{BASE}/scheduler/sync/jobs')
pp('STEP 14: List Scheduled Jobs', r)

# STEP 15: Stop Scheduler
r = requests.post(f'{BASE}/scheduler/sync/stop')
pp('STEP 15: Stop Scheduler', r)

# STEP 16: API Info
r = requests.get(f'{BASE}/info')
data = r.json()
print('\nSTEP 16: All Available Endpoints')
svc = data.get('service', 'N/A')
ver = data.get('version', 'N/A')
print(f'  Service: {svc} v{ver}')
for group, endpoints in data['endpoints'].items():
    print(f'  [{group}]')
    for path, desc in endpoints.items():
        print(f'    {path}: {desc}')
passed += 1

print()
print('=' * 70)
print(f'  RESULTS: {passed} passed, {failed} failed out of {passed + failed} steps')
if failed == 0:
    print('  ALL STEPS PASSED!')
else:
    print(f'  {failed} STEP(S) FAILED')
print('=' * 70)
