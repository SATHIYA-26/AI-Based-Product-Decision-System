"""Run multiple pipeline experiments and log them to MLflow.

Usage:
    cd backend
    python scripts/run_mlflow_experiments.py
"""

import os
import random
import sys
import logging
from datetime import datetime, timedelta


BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BACKEND_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from review_clustering.services.pipeline_service import PipelineService


def setup_logger() -> logging.Logger:
    """Configure logger for both console and file output."""
    logs_dir = os.path.join(BACKEND_DIR, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    log_file = os.path.join(logs_dir, "mlflow_experiments.log")

    logger = logging.getLogger("mlflow_experiments")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    return logger


def build_dataset(seed: int, size_per_theme: int = 8):
    random.seed(seed)
    now = datetime.utcnow()

    login_reviews = [
        "Login failed after latest update",
        "OTP login not working",
        "Cannot sign in to account",
        "Login screen freezes",
    ]
    payment_reviews = [
        "Payment failed during checkout",
        "Card transaction declined unexpectedly",
        "UPI payment timeout issue",
        "Unable to complete subscription payment",
    ]
    crash_reviews = [
        "App crashes on startup",
        "Application closes suddenly",
        "Crash observed while opening profile",
        "Frequent app crash after update",
    ]

    dataset = []
    themes = [login_reviews, payment_reviews, crash_reviews]
    for _ in range(size_per_theme):
        for theme in themes:
            text = random.choice(theme)
            ts = now - timedelta(days=random.randint(0, 14), hours=random.randint(0, 23))
            dataset.append({"text": text, "timestamp": ts.isoformat()})

    random.shuffle(dataset)
    return dataset


def main():
    logger = setup_logger()

    os.environ.setdefault("MLFLOW_ENABLED", "true")
    os.environ.setdefault("MLFLOW_TRACKING_URI", "file:./mlruns")
    os.environ.setdefault("MLFLOW_EXPERIMENT_NAME", "review-clustering-pipeline")

    logger.info("Starting MLflow experiment batch")
    logger.info("MLFLOW_TRACKING_URI=%s", os.environ.get("MLFLOW_TRACKING_URI"))
    logger.info("MLFLOW_EXPERIMENT_NAME=%s", os.environ.get("MLFLOW_EXPERIMENT_NAME"))

    seeds = [11, 22, 33]
    logger.info("Configured run seeds: %s", seeds)
    for idx, seed in enumerate(seeds, start=1):
        size_per_theme = 7 + idx
        logger.info("Run %s starting | seed=%s | size_per_theme=%s", idx, seed, size_per_theme)
        try:
            raw_items = build_dataset(seed=seed, size_per_theme=size_per_theme)
            result = PipelineService.run_pipeline(raw_items, save_to_db=True)

            cluster_count = len(result.get("cluster_summary", {}))
            execution_time_ms = result.get("execution_time_ms")
            run_id = result.get("run_id", "")
            saved = result.get("saved", False)

            logger.info(
                "Run %s completed | inputs=%s | clusters=%s | execution_time_ms=%s | saved=%s | run_id=%s",
                idx,
                len(raw_items),
                cluster_count,
                execution_time_ms,
                saved,
                run_id,
            )
        except Exception:
            logger.exception("Run %s failed", idx)

    logger.info("Experiment batch finished")
    logger.info("To view dashboard: mlflow ui --backend-store-uri ./mlruns")


if __name__ == "__main__":
    main()
