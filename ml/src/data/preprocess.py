"""Data preprocessing pipeline for RoomIQ sensor datasets."""

from pathlib import Path
from typing import Dict, Optional, Tuple
import pandas as pd
import numpy as np

from src.data.loader import load_raw_file, load_dataset_splits


def engineer_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """Engineer non-leaking calendar features derived solely from timestamp.

    These features depend strictly on the instantaneous timestamp of each
    observation and do not require lookahead or lookbehind across temporal splits.

    Args:
        df: Input DataFrame containing validated 'date' column.

    Returns:
        DataFrame with added temporal columns:
            - hour (0-23)
            - minute (0-59)
            - minute_of_day (0-1439)
            - day_of_week (0=Monday, 6=Sunday)
            - is_weekend (0 or 1)
    """
    processed = df.copy()
    dt = processed["date"].dt

    processed["hour"] = dt.hour.astype("int8")
    processed["minute"] = dt.minute.astype("int8")
    processed["minute_of_day"] = (dt.hour * 60 + dt.minute).astype("int16")
    processed["day_of_week"] = dt.dayofweek.astype("int8")
    processed["is_weekend"] = dt.dayofweek.isin([5, 6]).astype("int8")

    return processed


def preprocess_split(df: pd.DataFrame) -> pd.DataFrame:
    """Preprocess a single split independently.

    Ensures proper dtypes, extracts calendar features, validates no nulls,
    and returns a clean, modeling-ready DataFrame.

    Args:
        df: Raw validated DataFrame for the split.

    Returns:
        Cleaned, feature-engineered DataFrame.
    """
    # 1. Engineer non-leaking instantaneous temporal features
    processed = engineer_temporal_features(df)

    # 2. Strict type specification
    type_map = {
        "Temperature": "float64",
        "Humidity": "float64",
        "Light": "float64",
        "CO2": "float64",
        "HumidityRatio": "float64",
        "Occupancy": "int8",
        "hour": "int8",
        "minute": "int8",
        "minute_of_day": "int16",
        "day_of_week": "int8",
        "is_weekend": "int8",
    }
    processed = processed.astype(type_map)

    # Verify no missing values introduced
    if processed.isna().any().any():
        raise ValueError("Unexpected NaN values created during preprocessing.")

    return processed


def run_pipeline(
    raw_dir: Path,
    processed_dir: Path,
) -> Dict[str, pd.DataFrame]:
    """Execute the end-to-end preprocessing pipeline for all splits.

    Args:
        raw_dir: Path to directory containing raw dataset files.
        processed_dir: Path to directory where processed CSVs should be saved.

    Returns:
        Dictionary mapping split names to cleaned DataFrames.
    """
    processed_dir.mkdir(parents=True, exist_ok=True)
    splits = load_dataset_splits(raw_dir)

    processed_splits = {}
    output_names = {
        "training": "training_clean.csv",
        "test": "test_clean.csv",
        "test2": "test2_clean.csv",
    }

    for split_name, raw_df in splits.items():
        # Preprocess split independently (no cross-file merging or leak)
        clean_df = preprocess_split(raw_df)
        processed_splits[split_name] = clean_df

        # Save to disk
        out_path = processed_dir / output_names[split_name]
        clean_df.to_csv(out_path, index=False)
        print(f"Saved processed split '{split_name}' -> {out_path} ({len(clean_df):,} rows)")

    return processed_splits
