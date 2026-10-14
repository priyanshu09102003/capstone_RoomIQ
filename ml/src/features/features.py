"""Feature engineering and future target alignment for RoomIQ."""

from typing import Dict, List, Tuple
import pandas as pd
import numpy as np

BASE_SENSORS: List[str] = [
    "Temperature",
    "Humidity",
    "Light",
    "CO2",
    "HumidityRatio",
]

TARGET_COLUMNS: Dict[str, str] = {
    "occupancy": "target_occupancy_10m",
    "temperature": "target_temperature_10m",
    "humidity": "target_humidity_10m",
}


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Construct backward-looking features using strictly past and current observations.

    Never creates features using future sensor readings or future targets.
    Excludes row ID and index artifacts.

    Features generated:
    1. Base sensors: Temperature, Humidity, Light, CO2, HumidityRatio
    2. Calendar/cyclical: hour, day_of_week, is_weekend, sin_time, cos_time
    3. Backward lags: 1m, 5m, 10m for all 5 sensors
    4. Differences (change rates): 5m and 10m deltas for all 5 sensors
    5. Backward rolling statistics: 5m mean, 15m mean, 15m std for all 5 sensors

    Args:
        df: Input DataFrame containing 'date' and baseline sensor columns.

    Returns:
        DataFrame containing all engineered feature columns alongside 'date'.
    """
    feat_df = df.sort_values("date").copy().reset_index(drop=True)
    dt = feat_df["date"].dt

    # 1. Base instantaneous sensors
    for col in BASE_SENSORS:
        feat_df[col] = feat_df[col].astype("float64")

    # 2. Calendar and cyclical features
    minute_of_day = (dt.hour * 60 + dt.minute).astype("float64")
    feat_df["hour"] = dt.hour.astype("int8")
    feat_df["day_of_week"] = dt.dayofweek.astype("int8")
    feat_df["is_weekend"] = dt.dayofweek.isin([5, 6]).astype("int8")
    feat_df["sin_time"] = np.sin(2 * np.pi * minute_of_day / 1440.0).astype("float64")
    feat_df["cos_time"] = np.cos(2 * np.pi * minute_of_day / 1440.0).astype("float64")

    # 3. Backward lags and deltas (strictly <= t)
    for col in BASE_SENSORS:
        feat_df[f"{col}_lag_1m"] = feat_df[col].shift(1).astype("float64")
        feat_df[f"{col}_lag_5m"] = feat_df[col].shift(5).astype("float64")
        feat_df[f"{col}_lag_10m"] = feat_df[col].shift(10).astype("float64")
        feat_df[f"{col}_diff_5m"] = (feat_df[col] - feat_df[f"{col}_lag_5m"]).astype("float64")
        feat_df[f"{col}_diff_10m"] = (feat_df[col] - feat_df[f"{col}_lag_10m"]).astype("float64")

    # 4. Backward rolling statistics (strictly past window <= t)
    for col in BASE_SENSORS:
        feat_df[f"{col}_roll_mean_5m"] = (
            feat_df[col].rolling(window=5, min_periods=1).mean().astype("float64")
        )
        feat_df[f"{col}_roll_mean_15m"] = (
            feat_df[col].rolling(window=15, min_periods=1).mean().astype("float64")
        )
        feat_df[f"{col}_roll_std_15m"] = (
            feat_df[col].rolling(window=15, min_periods=1).std().fillna(0.0).astype("float64")
        )

    return feat_df


def align_future_targets(
    df: pd.DataFrame,
    horizon_minutes: int = 10,
    tolerance_seconds: int = 15,
) -> pd.DataFrame:
    """Align future ground-truth targets strictly by timestamp.

    Matches observation at time t with the ground-truth observation at
    time (t + horizon_minutes) +/- tolerance_seconds using asof merge.
    Does not blindly shift rows.

    Args:
        df: Input DataFrame with 'date', 'Occupancy', 'Temperature', 'Humidity'.
        horizon_minutes: Forecast horizon in minutes (default 10).
        tolerance_seconds: Max acceptable clock jitter in seconds (default 15).

    Returns:
        DataFrame with aligned future target columns:
            - target_occupancy_10m
            - target_temperature_10m
            - target_humidity_10m
    """
    sorted_df = df.sort_values("date").copy().reset_index(drop=True)

    # Construct target lookup table
    target_lookup = pd.DataFrame({
        "target_timestamp": sorted_df["date"],
        "query_time": sorted_df["date"] - pd.Timedelta(minutes=horizon_minutes),
        TARGET_COLUMNS["occupancy"]: sorted_df["Occupancy"].astype("int8"),
        TARGET_COLUMNS["temperature"]: sorted_df["Temperature"].astype("float64"),
        TARGET_COLUMNS["humidity"]: sorted_df["Humidity"].astype("float64"),
    }).sort_values("query_time").reset_index(drop=True)

    # Merge asof on query_time == date
    aligned = pd.merge_asof(
        sorted_df,
        target_lookup,
        left_on="date",
        right_on="query_time",
        tolerance=pd.Timedelta(seconds=tolerance_seconds),
        direction="nearest",
    )

    aligned = aligned.drop(columns=["query_time", "target_timestamp"])
    return aligned


def get_feature_column_names() -> List[str]:
    """Return explicit list of all predictor feature column names."""
    cols = list(BASE_SENSORS)
    cols.extend(["hour", "day_of_week", "is_weekend", "sin_time", "cos_time"])

    for col in BASE_SENSORS:
        cols.extend([
            f"{col}_lag_1m",
            f"{col}_lag_5m",
            f"{col}_lag_10m",
            f"{col}_diff_5m",
            f"{col}_diff_10m",
        ])

    for col in BASE_SENSORS:
        cols.extend([
            f"{col}_roll_mean_5m",
            f"{col}_roll_mean_15m",
            f"{col}_roll_std_15m",
        ])

    return cols


FEATURE_COLUMNS: List[str] = get_feature_column_names()


def prepare_modeling_split(
    df: pd.DataFrame,
    horizon_minutes: int = 10,
    max_lag_minutes: int = 10,
) -> Tuple[pd.DataFrame, Dict[str, pd.Series], Dict[str, int]]:
    """End-to-end preparation of a dataset split for modeling.

    Handles boundary trimming explicitly and documents row exclusions:
    - Excludes first max_lag_minutes rows due to unpopulated lag window.
    - Excludes last horizon_minutes rows due to lack of future target.

    Args:
        df: Cleaned split DataFrame.
        horizon_minutes: Forecast horizon (default 10).
        max_lag_minutes: Max lag window in minutes (default 10).

    Returns:
        Tuple of:
            - X: DataFrame containing only FEATURE_COLUMNS
            - y_dict: Dict with target Series ('occupancy', 'temperature', 'humidity')
            - exclusion_stats: Dict documenting row counts and exclusions
    """
    total_raw_rows = len(df)

    # 1. Feature construction
    feats = build_features(df)

    # 2. Target alignment
    aligned = align_future_targets(feats, horizon_minutes=horizon_minutes)

    # 3. Clean boundary exclusions
    # A. Lag initialization rows (head of split)
    valid_lags_mask = aligned[f"CO2_lag_{max_lag_minutes}m"].notna()
    head_dropped = int((~valid_lags_mask).sum())

    # B. Missing future target rows (tail of split)
    valid_target_mask = aligned[TARGET_COLUMNS["occupancy"]].notna()
    tail_dropped = int((~valid_target_mask).sum())

    # Retain strictly valid rows
    valid_mask = valid_lags_mask & valid_target_mask
    usable_df = aligned[valid_mask].copy().reset_index(drop=True)

    X = usable_df[FEATURE_COLUMNS].copy()
    y_dict = {
        "occupancy": usable_df[TARGET_COLUMNS["occupancy"]].astype("int8"),
        "temperature": usable_df[TARGET_COLUMNS["temperature"]].astype("float64"),
        "humidity": usable_df[TARGET_COLUMNS["humidity"]].astype("float64"),
        "date": usable_df["date"],
    }

    exclusion_stats = {
        "total_input_rows": total_raw_rows,
        "head_rows_dropped_for_lags": head_dropped,
        "tail_rows_dropped_for_horizon": tail_dropped,
        "total_rows_excluded": head_dropped + tail_dropped,
        "usable_samples": len(usable_df),
    }

    return X, y_dict, exclusion_stats
