# app/services/clustering_service.py

import hdbscan
import numpy as np
from typing import Dict


class ClusteringService:

    @staticmethod
    def cluster_embeddings(embeddings: np.ndarray) -> np.ndarray:
        if len(embeddings) == 0:
            return np.array([])

        # Ensure we have enough data points for clustering
        num_points = len(embeddings)
        
        # For very small datasets, adjust min_cluster_size
        # With only 1-2 points, HDBSCAN will fail, so handle gracefully
        if num_points < 2:
            # Single point - assign to cluster 0
            return np.array([0])
        
        # Dynamically adjust min_cluster_size based on dataset size
        min_cluster_size = min(2, max(1, num_points // 3))
        
        # HDBSCAN's min_samples should not exceed the number of points
        min_samples = min(1, num_points - 1)
        
        try:
            clusterer = hdbscan.HDBSCAN(
                min_cluster_size=min_cluster_size,
                min_samples=min_samples,
                metric="euclidean"
            )
            labels = clusterer.fit_predict(embeddings)
            return labels
        except ValueError as e:
            # If HDBSCAN still fails (e.g., "k must be less than or equal to the number of training points")
            # assign all points to a single cluster
            if "k must be" in str(e) or "number of training points" in str(e):
                return np.zeros(num_points, dtype=int)
            raise

    @staticmethod
    def compute_cluster_metadata(labels: np.ndarray) -> Dict[int, int]:
        cluster_counts = {}
        for label in labels:
            if label == -1:
                continue  # noise
            cluster_counts[label] = cluster_counts.get(label, 0) + 1

        return cluster_counts
