#!/usr/bin/env python
"""RoomIQ Preprocessing Pipeline CLI.

This script executes the complete Phase 2A data inspection, validation,
preprocessing, quality reporting, and exploratory visualization pipeline.

Can be run from within `ml/`:
    python run_preprocessing.py

Or from project root:
    python ml/run_preprocessing.py
"""

import sys
from pathlib import Path

# Ensure 'ml' directory or current script dir is on sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from src.data.loader import load_dataset_splits
from src.data.quality import generate_quality_report
from src.data.preprocess import run_pipeline
from src.data.visualize import generate_all_plots


def main():
    print("=" * 65)
    print(" ROOMIQ — PHASE 2A DATA INSPECTION & PREPROCESSING PIPELINE")
    print("=" * 65)

    base_dir = SCRIPT_DIR
    raw_dir = base_dir / "data" / "raw"
    processed_dir = base_dir / "data" / "processed"
    reports_dir = base_dir / "reports"
    figures_dir = reports_dir / "figures"

    print(f"\n[1/4] Loading raw sensor datasets from: {raw_dir}")
    raw_splits = load_dataset_splits(raw_dir)
    for name, df in raw_splits.items():
        print(f"  - Loaded split '{name}': {len(df):,} rows x {len(df.columns)} columns")

    print(f"\n[2/4] Generating data quality audit reports in: {reports_dir}")
    report_file = generate_quality_report(raw_splits, raw_dir, reports_dir)
    print(f"  - Generated Markdown report -> {report_file}")
    print(f"  - Generated summary statistics JSON -> {reports_dir / 'summary_statistics.json'}")

    print(f"\n[3/4] Running independent split preprocessing -> {processed_dir}")
    processed_splits = run_pipeline(raw_dir, processed_dir)
    for name, df in processed_splits.items():
        print(f"  - Clean split '{name}': {len(df):,} observations | features: {list(df.columns)}")

    print(f"\n[4/4] Generating exploratory data analysis plots -> {figures_dir}")
    generate_all_plots(processed_splits, figures_dir)
    print("  - Generated all EDA figures successfully.")

    print("\n" + "=" * 65)
    print(" PIPELINE COMPLETED SUCCESSFULLY")
    print(f" Processed files: {processed_dir}")
    print(f" Quality reports: {reports_dir}")
    print(f" EDA Figures:     {figures_dir}")
    print("=" * 65)


if __name__ == "__main__":
    main()
