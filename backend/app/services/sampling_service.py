import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


class SamplingService:

    @staticmethod
    def get_representative_samples(
        cleaned_texts,
        embeddings,
        cluster_labels,
        cluster_id,
        top_k=3
    ):

        # Get indices belonging to this cluster
        indices = [
            i for i, label in enumerate(cluster_labels)
            if label == cluster_id
        ]

        if not indices:
            return []

        cluster_embeddings = embeddings[indices]

        # Compute centroid
        centroid = np.mean(cluster_embeddings, axis=0).reshape(1, -1)

        # Compute cosine similarity
        similarities = cosine_similarity(cluster_embeddings, centroid).flatten()

        # Sort by similarity
        sorted_indices = np.argsort(similarities)[::-1]

        # Select top_k
        top_indices = sorted_indices[:top_k]

        representative_reviews = [
            cleaned_texts[indices[i]]
            for i in top_indices
        ]

        return representative_reviews