# MLflow Experiment Logging Guide

This document explains how MLflow was integrated and how to capture required screenshots for:

- logging parameters, metrics, and outputs
- inspecting multiple experiment runs
- recording dashboards, plots, and logs

## 1. What was implemented

MLflow integration is now built into the backend pipeline flow.

Integrated files:

- src/review_clustering/services/experiment_tracking_service.py
- src/review_clustering/services/pipeline_service.py
- scripts/run_mlflow_experiments.py

Dependencies added:

- mlflow
- matplotlib

## 2. What gets logged for each run

### Parameters

- save_to_db
- min_cluster_size_threshold
- tracking_uri
- experiment_name
- run_id_saved

### Metrics

- execution_time_ms
- num_inputs
- num_filtered
- num_cleaned
- num_clusters
- noise_points
- max_cluster_frequency
- avg_cluster_frequency
- max_priority_score
- avg_priority_score
- avg_cluster_sentiment
- avg_cluster_trend

### Artifacts (outputs)

- pipeline_outputs/cluster_summary.json
- pipeline_outputs/metrics_snapshot.json
- pipeline_outputs/pipeline_result.json
- pipeline_outputs/top_clusters.csv
- pipeline_outputs/cluster_frequency_plot.png (when matplotlib is available)

## 3. Environment variables (optional)

You can customize tracking location and experiment name.

Windows PowerShell:

```powershell
$env:MLFLOW_ENABLED="true"
$env:MLFLOW_TRACKING_URI="file:./mlruns"
$env:MLFLOW_EXPERIMENT_NAME="review-clustering-pipeline"
```

Defaults are already set in code if these are not provided.

## 4. Setup commands

Run from repository root:

```powershell
cd D:\AI\backend
pip install -r requirements.txt
```

## 5. Generate multiple experiment runs

Run this script to create multiple pipeline runs:

```powershell
cd D:\AI\backend
python scripts/run_mlflow_experiments.py
```

This script automatically triggers multiple runs so you can compare them in MLflow.

## 6. Open MLflow UI

Start UI:

```powershell
cd D:\AI\backend
mlflow ui --backend-store-uri ./mlruns --port 5001
```

Open in browser:

- http://127.0.0.1:5001

## 7. Screenshot checklist (for report/demo)

Take these screenshots in order:

1. MLflow experiment page showing run list (multiple runs visible).
2. Single run details page with Parameters section expanded.
3. Single run details page with Metrics section expanded.
4. Artifacts tab showing logged files (json/csv/png).
5. Opened cluster_frequency_plot.png from artifacts.
6. MLflow charts panel showing metric comparison across runs.
7. Terminal output of scripts/run_mlflow_experiments.py execution.
8. Optional: backend API /process-reviews call output if you want runtime evidence.

## 8. How to inspect multiple runs

In MLflow UI:

1. Open experiment review-clustering-pipeline.
2. Select two or more runs using checkboxes.
3. Click Compare.
4. Inspect differences in execution_time_ms, num_clusters, avg_priority_score.

## 9. Notes for defense explanation

Use this concise explanation:

"MLflow was integrated as a non-blocking experiment tracker inside the pipeline service. Every pipeline execution logs parameters, metrics, and artifacts. Multiple runs can be compared in MLflow UI to evaluate pipeline behavior and consistency. Artifacts include JSON summaries, CSV output, and a generated plot for visual analysis."

## 10. Troubleshooting

### mlflow command not found

Use:

```powershell
python -m mlflow ui --backend-store-uri ./mlruns --port 5001
```

### No runs visible

- Ensure the script ran successfully.
- Confirm tracking URI points to backend/mlruns.

### Plot not generated

- Install matplotlib.
- Re-run scripts/run_mlflow_experiments.py.
