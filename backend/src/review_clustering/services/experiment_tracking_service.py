"""MLflow experiment tracking for pipeline runs."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional


class ExperimentTrackingService:
    """Logs pipeline parameters, metrics, and artifacts to MLflow.

    Logging is best-effort: failures are swallowed so the main pipeline flow
    continues even if MLflow is unavailable.
    """

    @staticmethod
    def _is_enabled() -> bool:
        return os.getenv("MLFLOW_ENABLED", "true").lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _import_mlflow():
        import mlflow

        return mlflow

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except Exception:
            return default

    @staticmethod
    def _build_metrics(
        cluster_summary: Dict[int, Dict[str, Any]],
        cluster_labels: List[int],
        execution_time_ms: int,
        num_inputs: int,
        num_cleaned: int,
        num_filtered: int,
    ) -> Dict[str, float]:
        num_clusters = len(cluster_summary)
        frequencies = [ExperimentTrackingService._safe_float(v.get("frequency", 0)) for v in cluster_summary.values()]
        priorities = [ExperimentTrackingService._safe_float(v.get("priority_score", 0)) for v in cluster_summary.values()]
        sentiments = [ExperimentTrackingService._safe_float(v.get("avg_sentiment", 0)) for v in cluster_summary.values()]
        trends = [ExperimentTrackingService._safe_float(v.get("trend_score", 0)) for v in cluster_summary.values()]
        noise_points = sum(1 for label in cluster_labels if label == -1)

        return {
            "execution_time_ms": float(execution_time_ms),
            "num_inputs": float(num_inputs),
            "num_filtered": float(num_filtered),
            "num_cleaned": float(num_cleaned),
            "num_clusters": float(num_clusters),
            "noise_points": float(noise_points),
            "max_cluster_frequency": max(frequencies) if frequencies else 0.0,
            "avg_cluster_frequency": (sum(frequencies) / len(frequencies)) if frequencies else 0.0,
            "max_priority_score": max(priorities) if priorities else 0.0,
            "avg_priority_score": (sum(priorities) / len(priorities)) if priorities else 0.0,
            "avg_cluster_sentiment": (sum(sentiments) / len(sentiments)) if sentiments else 0.0,
            "avg_cluster_trend": (sum(trends) / len(trends)) if trends else 0.0,
        }

    @staticmethod
    def _write_artifacts(
        temp_dir: str,
        cluster_summary: Dict[int, Dict[str, Any]],
        result_payload: Dict[str, Any],
        metrics: Dict[str, float],
    ) -> None:
        cluster_summary_path = os.path.join(temp_dir, "cluster_summary.json")
        with open(cluster_summary_path, "w", encoding="utf-8") as f:
            json.dump(cluster_summary, f, indent=2, default=str)

        metrics_path = os.path.join(temp_dir, "metrics_snapshot.json")
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)

        run_payload_path = os.path.join(temp_dir, "pipeline_result.json")
        with open(run_payload_path, "w", encoding="utf-8") as f:
            json.dump(result_payload, f, indent=2, default=str)

        top_clusters = sorted(
            cluster_summary.items(),
            key=lambda kv: ExperimentTrackingService._safe_float(kv[1].get("priority_score", 0.0)),
            reverse=True,
        )[:10]
        csv_path = os.path.join(temp_dir, "top_clusters.csv")
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("cluster_id,frequency,priority_score,avg_sentiment,trend_score,label\n")
            for cluster_id, item in top_clusters:
                label = str(item.get("label", "")).replace(",", " ")
                f.write(
                    f"{cluster_id},{item.get('frequency', 0)},{item.get('priority_score', 0)},"
                    f"{item.get('avg_sentiment', 0)},{item.get('trend_score', 0)},{label}\n"
                )

        # Optional artifact plot; if matplotlib is unavailable we still log JSON/CSV.
        try:
            import matplotlib.pyplot as plt

            if top_clusters:
                labels = [str(cluster_id) for cluster_id, _ in top_clusters]
                values = [ExperimentTrackingService._safe_float(item.get("frequency", 0)) for _, item in top_clusters]
                plt.figure(figsize=(8, 4.5))
                plt.bar(labels, values)
                plt.title("Top Cluster Frequencies")
                plt.xlabel("Cluster ID")
                plt.ylabel("Frequency")
                plt.tight_layout()
                plot_path = os.path.join(temp_dir, "cluster_frequency_plot.png")
                plt.savefig(plot_path)
                plt.close()
        except Exception:
            pass

    @staticmethod
    def log_pipeline_run(
        *,
        num_inputs: int,
        num_filtered: int,
        num_cleaned: int,
        save_to_db: bool,
        execution_time_ms: int,
        cluster_labels: List[int],
        cluster_summary: Dict[int, Dict[str, Any]],
        run_id: Optional[str],
        min_cluster_size_threshold: int,
    ) -> None:
        """Record pipeline run details to MLflow."""

        if not ExperimentTrackingService._is_enabled():
            return

        try:
            mlflow = ExperimentTrackingService._import_mlflow()
        except Exception:
            return

        tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "file:./mlruns")
        experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "review-clustering-pipeline")

        try:
            mlflow.set_tracking_uri(tracking_uri)
            mlflow.set_experiment(experiment_name)

            metrics = ExperimentTrackingService._build_metrics(
                cluster_summary=cluster_summary,
                cluster_labels=cluster_labels,
                execution_time_ms=execution_time_ms,
                num_inputs=num_inputs,
                num_cleaned=num_cleaned,
                num_filtered=num_filtered,
            )

            run_name = f"pipeline-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
            with mlflow.start_run(run_name=run_name):
                mlflow.log_params(
                    {
                        "save_to_db": str(save_to_db).lower(),
                        "min_cluster_size_threshold": min_cluster_size_threshold,
                        "tracking_uri": tracking_uri,
                        "experiment_name": experiment_name,
                        "run_id_saved": run_id or "",
                    }
                )
                mlflow.log_metrics(metrics)

                payload = {
                    "run_id": run_id,
                    "execution_time_ms": execution_time_ms,
                    "num_inputs": num_inputs,
                    "num_filtered": num_filtered,
                    "num_cleaned": num_cleaned,
                    "num_clusters": len(cluster_summary),
                    "cluster_summary": cluster_summary,
                }

                with tempfile.TemporaryDirectory() as temp_dir:
                    ExperimentTrackingService._write_artifacts(
                        temp_dir=temp_dir,
                        cluster_summary=cluster_summary,
                        result_payload=payload,
                        metrics=metrics,
                    )
                    mlflow.log_artifacts(temp_dir, artifact_path="pipeline_outputs")
        except Exception:
            # Keep tracking non-blocking for production flow reliability.
            return
