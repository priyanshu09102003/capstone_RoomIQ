#!/usr/bin/env python
"""RoomIQ Model Training & Evaluation CLI.

Executes Phase 2B training pipeline:
1. Loads cleaned dataset splits.
2. Constructs non-leaking features and aligns future targets (10-min horizon).
3. Fits Occupancy, Temperature, and Humidity models and baselines on chronological training set.
4. Evaluates all models on Validation, Test 1 (datatest), and Test 2 (datatest2) sets.
5. Serializes models and metadata to `ml/artifacts/`.
6. Generates evaluation report and diagnostic plots in `ml/reports/`.

Usage from ml directory:
    python run_training.py

Usage from project root:
    python ml/run_training.py
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from src.models.trainer import run_training_pipeline


def main():
    print("=" * 65)
    print(" ROOMIQ — PHASE 2B MODEL TRAINING & EVALUATION PIPELINE")
    print("=" * 65)

    base_dir = SCRIPT_DIR
    data_dir = base_dir / "data" / "processed"
    artifacts_dir = base_dir / "artifacts"
    reports_dir = base_dir / "reports"

    metadata = run_training_pipeline(
        data_dir=data_dir,
        artifacts_dir=artifacts_dir,
        reports_dir=reports_dir,
    )

    metrics = metadata["metrics"]
    print("\n--- SUMMARY OF TEST RESULTS (Test Set 2 — 9,732 samples) ---")
    print(f"Occupancy Classifier F1-Score: {metrics['test2']['occupancy']['model']['f1']:.4f} (Baseline: {metrics['test2']['occupancy']['baseline']['f1']:.4f})")
    print(f"Temperature Regressor MAE:     {metrics['test2']['temperature']['model']['mae']:.4f} °C (Baseline: {metrics['test2']['temperature']['baseline']['mae']:.4f} °C)")
    print(f"Humidity Regressor MAE:        {metrics['test2']['humidity']['model']['mae']:.4f} %  (Baseline: {metrics['test2']['humidity']['baseline']['mae']:.4f} %)")


if __name__ == "__main__":
    main()
