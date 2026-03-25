import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from review_clustering.services.persistence_service import PersistenceService

runs = PersistenceService.list_recent_runs(1)
print('Recent runs:', len(runs))
if runs:
    run = runs[0]
    print('Latest run:', run.get('run_id'))
    clusters = run.get('clusters', [])
    print('Clusters in run:', len(clusters))
    for cluster in clusters:
        label = cluster.get('label', 'N/A')
        freq = cluster.get('frequency', 0)
        print('  Cluster: label="{}" freq={}'.format(label, freq))
else:
    print('No runs found')
