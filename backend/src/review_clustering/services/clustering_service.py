# app/services/clustering_service.py

import hdbscan
import numpy as np
from typing import Dict


class ClusteringService:

    @staticmethod
    def cluster_embeddings(embeddings: np.ndarray) -> np.ndarray:
        if len(embeddings) == 0:
            return np.array([])

        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=2,
            min_samples=1,
            metric="euclidean"
        )

        labels = clusterer.fit_predict(embeddings)
        return labels

    @staticmethod
    def compute_cluster_metadata(labels: np.ndarray) -> Dict[int, int]:
        cluster_counts = {}
        for label in labels:
            if label == -1:
                continue  # noise
            cluster_counts[label] = cluster_counts.get(label, 0) + 1

        return cluster_counts
