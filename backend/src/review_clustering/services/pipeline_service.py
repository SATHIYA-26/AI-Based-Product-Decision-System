from typing import List, Dict, Any
import numpy as np
import time

from review_clustering.services.data_filter_service import DataFilterService
from review_clustering.services.preprocessing_service import PreprocessingService
from review_clustering.services.embedding_service import EmbeddingService
from review_clustering.services.sentiment_service import SentimentService
from review_clustering.services.clustering_service import ClusteringService
from review_clustering.services.priority_service import PriorityService
from review_clustering.services.sampling_service import SamplingService
from review_clustering.services.persistence_service import PersistenceService

# new helpers
from review_clustering.services.trend_service import TrendService
from review_clustering.services.llm_service import LLMService


class PipelineService:

    @staticmethod
    def run_pipeline(raw_items: List[Any], save_to_db: bool = True) -> Dict:
        """Execute the full pipeline and optionally persist results to database.
        
        Args:
            raw_items: List of strings or dicts with 'text' and optional 'timestamp'
            save_to_db: Whether to persist cluster results to the database
            
        Returns:
            Dict with pipeline results and (if saved) a run_id for later retrieval
        """
        
        start_time = time.time()
        # accomodate both simple strings and dicts containing timestamps

        MIN_CLUSTER_SIZE_THRESHOLD = 3  # Only show clusters with >= 3 reviews

        filtered = DataFilterService.filter_reviews(raw_items)

        if not filtered:
            return {"error": "No valid reviews after filtering."}

        # split text and timestamps if present
        if isinstance(filtered[0], dict):
            texts = [item["text"] for item in filtered]
            timestamps = [item.get("timestamp") for item in filtered]
        else:
            texts = filtered
            timestamps = [None] * len(texts)

        cleaned_texts = PreprocessingService.batch_clean(texts)

        # Remove empty cleaned texts and keep timestamps in sync
        zipped = [
            (txt, ts)
            for txt, ts in zip(cleaned_texts, timestamps)
            if txt.strip() != ""
        ]
        if not zipped:
            return {"error": "No valid reviews after preprocessing."}

        cleaned_texts, timestamps = zip(*zipped)
        cleaned_texts = list(cleaned_texts)
        timestamps = list(timestamps)

        # Remove duplicates after preprocessing (keep first timestamp)
        seen = set()
        unique_texts = []
        unique_timestamps = []
        for txt, ts in zip(cleaned_texts, timestamps):
            if txt in seen:
                continue
            seen.add(txt)
            unique_texts.append(txt)
            unique_timestamps.append(ts)

        cleaned_texts = unique_texts
        timestamps = unique_timestamps

        if not cleaned_texts:
            return {"error": "No valid reviews after preprocessing."}

        embeddings = EmbeddingService.generate_embeddings(cleaned_texts)

      
        sentiment_scores = SentimentService.batch_sentiment(cleaned_texts)

        cluster_labels = ClusteringService.cluster_embeddings(embeddings)

       
        cluster_counts = ClusteringService.compute_cluster_metadata(cluster_labels)

        max_frequency = max(cluster_counts.values()) if cluster_counts else 1

        cluster_summary = {}

        for cluster_id, frequency in cluster_counts.items():

            cluster_id = int(cluster_id)

            # Skip noise cluster
            if cluster_id == -1:
                continue

            # Skip small clusters (real-world filtering)
            if frequency < MIN_CLUSTER_SIZE_THRESHOLD:
                continue

            indices = [
                i for i, label in enumerate(cluster_labels)
                if label == cluster_id
            ]

            if not indices:
                continue

            avg_sentiment = float(
                np.mean([sentiment_scores[i] for i in indices])
            )

            # compute trend from timestamps (if available)
            trend_score = TrendService.compute_weekly_growth(indices, timestamps)

            priority_score = PriorityService.compute_priority(
                frequency,
                max_frequency,
                avg_sentiment,
                trend_score
            )

            representative_reviews = SamplingService.get_representative_samples(
                cleaned_texts,
                embeddings,
                cluster_labels,
                cluster_id,
                top_k=3
            )

            # generate LLM-powered summary & label
            try:
                summary = LLMService.generate_issue_summary(representative_reviews)
            except Exception:
                summary = ""  # fail gracefully

            try:
                label = LLMService.generate_label(representative_reviews)
            except Exception:
                label = ""

            cluster_summary[cluster_id] = {
                "frequency": frequency,
                "avg_sentiment": avg_sentiment,
                "priority_score": priority_score,
                "trend_score": trend_score,
                "summary": summary,
                "label": label,
                "representative_reviews": representative_reviews
            }

        execution_time_ms = int((time.time() - start_time) * 1000)
        
        result = {
            "cleaned_texts": cleaned_texts,
            "timestamps": timestamps,
            "sentiments": sentiment_scores,
            "cluster_labels": cluster_labels.tolist(),
            "cluster_summary": cluster_summary,
            "execution_time_ms": execution_time_ms
        }
        
        # save to database if requested
        if save_to_db:
            try:
                run_id = PersistenceService.save_pipeline_run(
                    num_inputs=len(raw_items),
                    num_cleaned=len(cleaned_texts),
                    cluster_summary=cluster_summary,
                    execution_time_ms=execution_time_ms
                )
                result["run_id"] = run_id
                result["saved"] = True
            except Exception as e:
                result["saved"] = False
                result["save_error"] = str(e)
        
        return result
