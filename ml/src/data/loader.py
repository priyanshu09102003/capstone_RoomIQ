"""Data loading and validation utilities for RoomIQ sensor datasets."""

from pathlib import Path
from typing import Dict, List, Union
import pandas as pd
import numpy as np

REQUIRED_COLUMNS: List[str] = [
    "date",
    "Temperature",
    "Humidity",
    "Light",
    "CO2",
    "HumidityRatio",
    "Occupancy",
]

NUMERIC_COLUMNS: List[str] = [
    "Temperature",
    "Humidity",
    "Light",
    "CO2",
    "HumidityRatio",
]


def validate_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Validate presence and types of required RoomIQ sensor columns.

    Args:
        df: Input DataFrame to validate.

    Returns:
        Validated DataFrame with standardized data types.

    Raises:
        ValueError: If required columns are missing, data types are malformed,
            or values violate domain constraints.
    """
    if df.empty:
        raise ValueError("DataFrame is empty; no observations to process.")

    # Check for required columns
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in dataset: {missing}")

    validated = df.copy()

    # Drop any leftover index column if present (e.g., 'Unnamed: 0')
    if "Unnamed: 0" in validated.columns:
        validated = validated.drop(columns=["Unnamed: 0"])

    # Reset index to ensure raw row IDs are not preserved as predictive features
    validated = validated.reset_index(drop=True)

    # 1. Parse and validate date
    try:
        cleaned_dates = validated["date"].astype(str).str.strip("\"' ")
        try:
            validated["date"] = pd.to_datetime(cleaned_dates, format="%Y-%m-%d %H:%M:%S", errors="raise")
        except Exception:
            validated["date"] = pd.to_datetime(cleaned_dates, errors="raise")
    except Exception as exc:
        raise ValueError(f"Failed to parse 'date' column into datetime: {exc}") from exc

    if validated["date"].isna().any():
        raise ValueError("Null or unparseable timestamps detected in 'date' column.")

    # 2. Parse and validate numeric features
    for col in NUMERIC_COLUMNS:
        try:
            validated[col] = pd.to_numeric(validated[col], errors="raise").astype("float64")
        except Exception as exc:
            raise ValueError(f"Failed to convert column '{col}' to float: {exc}") from exc

        if validated[col].isna().any():
            raise ValueError(f"Null or NaN values detected in column '{col}'.")

    # Domain range sanity checks
    if (validated["Light"] < 0).any():
        raise ValueError("Light values must be non-negative.")
    if (validated["CO2"] < 0).any():
        raise ValueError("CO2 values must be non-negative.")
    if (validated["HumidityRatio"] < 0).any():
        raise ValueError("HumidityRatio values must be non-negative.")

    # 3. Parse and validate Occupancy target
    try:
        validated["Occupancy"] = pd.to_numeric(validated["Occupancy"], errors="raise").astype("int64")
    except Exception as exc:
        raise ValueError(f"Failed to convert 'Occupancy' to integer: {exc}") from exc

    if validated["Occupancy"].isna().any():
        raise ValueError("Null or NaN values detected in 'Occupancy' column.")

    invalid_labels = set(validated["Occupancy"].unique()) - {0, 1}
    if invalid_labels:
        raise ValueError(f"Occupancy column must only contain binary values {0, 1}, found: {invalid_labels}")

    return validated[REQUIRED_COLUMNS]


def load_raw_file(file_path: Union[str, Path]) -> pd.DataFrame:
    """Load a raw RoomIQ sensor file (.txt or .csv), discarding raw row IDs.

    Args:
        file_path: Path to the raw text file.

    Returns:
        Validated pandas DataFrame with standard columns.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If file is empty or cannot be parsed.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if path.stat().st_size == 0:
        raise ValueError(f"File is empty (0 bytes): {path}")

    try:
        # Using index_col=0 ensures the leading row ID in UCI files is loaded as index
        # rather than being misinterpreted as a feature column.
        df = pd.read_csv(path, index_col=0)
    except pd.errors.EmptyDataError as exc:
        raise ValueError(f"File contains no data: {path}") from exc
    except Exception as exc:
        raise ValueError(f"Failed to read CSV from {path}: {exc}") from exc

    # If the file didn't have a leading index and date ended up in index:
    if "date" not in df.columns and df.index.name == "date":
        df = df.reset_index()

    # Validate and standardize
    return validate_schema(df)


def load_dataset_splits(data_dir: Union[str, Path]) -> Dict[str, pd.DataFrame]:
    """Load all standard raw dataset files from the raw data directory.

    Args:
        data_dir: Path to directory containing raw files.

    Returns:
        Dictionary mapping split names ('training', 'test', 'test2') to DataFrames.
    """
    raw_dir = Path(data_dir)
    splits = {
        "training": raw_dir / "datatraining.txt",
        "test": raw_dir / "datatest.txt",
        "test2": raw_dir / "datatest2.txt",
    }

    loaded = {}
    for split_name, split_path in splits.items():
        loaded[split_name] = load_raw_file(split_path)

    return loaded
