"""Unit tests for RoomIQ data loading, validation, and preprocessing modules."""

from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from src.data.loader import (
    REQUIRED_COLUMNS,
    load_raw_file,
    load_dataset_splits,
    validate_schema,
)
from src.data.preprocess import (
    engineer_temporal_features,
    preprocess_split,
    run_pipeline,
)
from src.data.quality import (
    analyze_split_quality,
    analyze_inter_split_gaps,
)


@pytest.fixture
def valid_sample_df() -> pd.DataFrame:
    """Fixture providing a valid synthetic sample DataFrame matching UCI format."""
    return pd.DataFrame({
        "date": [
            "2015-02-04 17:51:00",
            "2015-02-04 17:52:00",
            "2015-02-04 17:53:00",
        ],
        "Temperature": [23.18, 23.15, 23.10],
        "Humidity": [27.27, 27.26, 27.20],
        "Light": [426.0, 429.0, 426.0],
        "CO2": [721.25, 714.00, 713.50],
        "HumidityRatio": [0.00479, 0.00478, 0.00477],
        "Occupancy": [1, 1, 0],
    })


@pytest.fixture
def raw_data_dir() -> Path:
    """Path to the real raw data directory."""
    return Path(__file__).resolve().parent.parent / "data" / "raw"


class TestDataLoaderAndValidation:
    """Tests for raw file loading, schema validation, and type conversions."""

    def test_load_raw_real_splits(self, raw_data_dir):
        """Verify real UCI raw files load with expected row counts and columns."""
        splits = load_dataset_splits(raw_data_dir)

        assert "training" in splits
        assert "test" in splits
        assert "test2" in splits

        assert len(splits["training"]) == 8143
        assert len(splits["test"]) == 2665
        assert len(splits["test2"]) == 9752

        for name, df in splits.items():
            assert list(df.columns) == REQUIRED_COLUMNS
            assert df.isna().sum().sum() == 0
            assert pd.api.types.is_datetime64_any_dtype(df["date"])
            assert pd.api.types.is_float_dtype(df["Temperature"])
            assert pd.api.types.is_float_dtype(df["Light"])
            assert set(df["Occupancy"].unique()).issubset({0, 1})

    def test_row_id_discarded(self, raw_data_dir):
        """Verify leading row ID column from raw files is not treated as a feature."""
        df = load_raw_file(raw_data_dir / "datatraining.txt")
        # Ensure only the 7 standard columns are present
        assert len(df.columns) == 7
        assert "Unnamed: 0" not in df.columns
        assert "index" not in df.columns
        assert list(df.columns) == REQUIRED_COLUMNS

    def test_missing_required_column_raises(self, valid_sample_df):
        """Verify ValueError is raised if any mandatory column is missing."""
        incomplete_df = valid_sample_df.drop(columns=["Light"])
        with pytest.raises(ValueError, match="Missing required columns.*Light"):
            validate_schema(incomplete_df)

    def test_timestamp_parsing_quoted_and_unquoted(self):
        """Verify parser handles both quoted and unquoted timestamp representations."""
        df_quoted = pd.DataFrame({
            "date": ['"2015-02-04 17:51:00"'],
            "Temperature": [21.0],
            "Humidity": [25.0],
            "Light": [100.0],
            "CO2": [500.0],
            "HumidityRatio": [0.004],
            "Occupancy": [1],
        })
        validated_q = validate_schema(df_quoted)
        assert validated_q["date"].iloc[0] == pd.Timestamp("2015-02-04 17:51:00")

        df_unquoted = pd.DataFrame({
            "date": ["2015-02-11 14:48:00"],
            "Temperature": [21.0],
            "Humidity": [25.0],
            "Light": [100.0],
            "CO2": [500.0],
            "HumidityRatio": [0.004],
            "Occupancy": [1],
        })
        validated_u = validate_schema(df_unquoted)
        assert validated_u["date"].iloc[0] == pd.Timestamp("2015-02-11 14:48:00")

    def test_malformed_timestamp_raises(self, valid_sample_df):
        """Verify ValueError is raised when dates cannot be parsed."""
        corrupt_df = valid_sample_df.copy()
        corrupt_df.loc[0, "date"] = "invalid_timestamp_string"
        with pytest.raises(ValueError, match="Failed to parse 'date'"):
            validate_schema(corrupt_df)

    def test_malformed_numeric_raises(self, valid_sample_df):
        """Verify ValueError is raised when sensor columns contain non-numeric data."""
        corrupt_df = valid_sample_df.copy()
        corrupt_df["CO2"] = corrupt_df["CO2"].astype(object)
        corrupt_df.loc[1, "CO2"] = "not_a_number"
        with pytest.raises(ValueError, match="Failed to convert column 'CO2'"):
            validate_schema(corrupt_df)

    def test_invalid_occupancy_labels_raises(self, valid_sample_df):
        """Verify ValueError is raised when Occupancy contains non-binary values."""
        corrupt_df = valid_sample_df.copy()
        corrupt_df.loc[0, "Occupancy"] = 2
        with pytest.raises(ValueError, match="Occupancy column must only contain binary values"):
            validate_schema(corrupt_df)

    def test_negative_physical_values_raises(self, valid_sample_df):
        """Verify ValueError is raised for physically impossible sensor values."""
        corrupt_df = valid_sample_df.copy()
        corrupt_df.loc[0, "Light"] = -10.0
        with pytest.raises(ValueError, match="Light values must be non-negative"):
            validate_schema(corrupt_df)

    def test_empty_dataframe_raises(self):
        """Verify ValueError is raised for an empty DataFrame."""
        empty_df = pd.DataFrame(columns=REQUIRED_COLUMNS)
        with pytest.raises(ValueError, match="DataFrame is empty"):
            validate_schema(empty_df)

    def test_empty_file_raises(self, tmp_path):
        """Verify ValueError is raised for a 0-byte file."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")
        with pytest.raises(ValueError, match="File is empty"):
            load_raw_file(empty_file)


class TestPreprocessingAndFeatureEngineering:
    """Tests for feature engineering, split independence, and pipeline execution."""

    def test_engineer_temporal_features(self, valid_sample_df):
        """Verify calendar features are calculated accurately without lookahead."""
        validated = validate_schema(valid_sample_df)
        engineered = engineer_temporal_features(validated)

        assert "hour" in engineered.columns
        assert "minute" in engineered.columns
        assert "minute_of_day" in engineered.columns
        assert "day_of_week" in engineered.columns
        assert "is_weekend" in engineered.columns

        # Row 0 is 2015-02-04 17:51:00 (Wednesday = dayofweek 2)
        assert engineered.loc[0, "hour"] == 17
        assert engineered.loc[0, "minute"] == 51
        assert engineered.loc[0, "minute_of_day"] == 17 * 60 + 51
        assert engineered.loc[0, "day_of_week"] == 2
        assert engineered.loc[0, "is_weekend"] == 0

    def test_preprocess_split_preserves_row_count(self, valid_sample_df):
        """Verify preprocessing does not drop or add any synthetic rows."""
        validated = validate_schema(valid_sample_df)
        clean = preprocess_split(validated)
        assert len(clean) == len(valid_sample_df)
        assert clean.isna().sum().sum() == 0

    def test_run_pipeline_creates_clean_files(self, raw_data_dir, tmp_path):
        """Verify full pipeline generates non-empty CSV files for all splits."""
        output_dir = tmp_path / "processed"
        splits = run_pipeline(raw_data_dir, output_dir)

        assert (output_dir / "training_clean.csv").exists()
        assert (output_dir / "test_clean.csv").exists()
        assert (output_dir / "test2_clean.csv").exists()

        assert len(splits["training"]) == 8143
        assert len(splits["test"]) == 2665
        assert len(splits["test2"]) == 9752


class TestQualityAuditAndGaps:
    """Tests for audit metrics and inter-split gap computation."""

    def test_analyze_inter_split_gaps(self, raw_data_dir):
        """Verify inter-split gaps match known UCI experimental protocol."""
        splits = load_dataset_splits(raw_data_dir)
        gaps = analyze_inter_split_gaps(splits)

        assert len(gaps) == 2
        # Transition 1: test -> training (~7.13 hours)
        assert gaps[0]["from_split"] == "test"
        assert gaps[0]["to_split"] == "training"
        assert 7.0 <= gaps[0]["gap_hours"] <= 7.2

        # Transition 2: training -> test2 (~29.25 hours)
        assert gaps[1]["from_split"] == "training"
        assert gaps[1]["to_split"] == "test2"
        assert 29.0 <= gaps[1]["gap_hours"] <= 29.5
