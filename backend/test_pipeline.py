import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from review_clustering.services.pipeline_service import PipelineService

# Test data
feedback = [
    'Login not working after update',
    'Login failed multiple times', 
    'Unable to login to my account',
    'Payment processing failed',
    'Card payment declined',
    'App crashes when opening profile',
    'App crash after update',
    'Profile section not loading'
]

print('Running pipeline with test data...')
result = PipelineService.run_pipeline(feedback, save_to_db=True)
print('Pipeline completed! Run ID:', result.get('run_id'))
print('Saved to DB:', result.get('saved', False))
if 'save_error' in result:
    print('Save error:', result['save_error'])
print('Clusters created:', len(result.get('cluster_summary', {})))
for cluster_id, data in result.get('cluster_summary', {}).items():
    label = data.get('label', 'N/A')
    freq = data.get('frequency', 0)
    print('  Cluster {}: label="{}" freq={}'.format(cluster_id, label, freq))
