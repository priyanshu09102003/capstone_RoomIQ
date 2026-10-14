"""Unit tests for RoomIQ feature engineering, target alignment, and model inference."""

from pathlib import Path
import pytest
import pandas as pd
import numpy as np
import joblib

from src.features.features import (
    align_future_targets,
    build_features,
    prepare_modeling_split,
    get_feature_column_names,
    FEATURE_COLUMNS,
    TARGET_COLUMNS,
)
from src.models.models import (
    PersistenceRegressor,
    create_occupancy_classifier,
    create_temperature_regressor,
    create_humidity_regressor,
)
from src.models.predictor import RoomIQPredictor


@pytest.fixture
def sample_clean_df() -> pd.DataFrame:
    """Fixture generating a 30-minute synthetic time-series of cleaned observations."""
    timestamps = pd.date_range("2015-02-04 12:00:00", periods=30, freq="1min")
    return pd.DataFrame({
        "date": timestamps,
        "Temperature": 20.0 + np.sin(np.linspace(0, 3, 30)),
        "Humidity": 25.0 + np.cos(np.linspace(0, 3, 30)),
        "Light": np.where(np.arange(30) > 10, 400.0, 0.0),
        "CO2": 500.0 + np.arange(30) * 10.0,
        "HumidityRatio": 0.0035 + np.linspace(0, 0.001, 30),
        "Occupancy": np.where(np.arange(30) > 10, 1, 0),
        "hour": 12,
        "minute": np.arange(30),
        "minute_of_day": 12 * 60 + np.arange(30),
        "day_of_week": 2,
        "is_weekend": 0,
    })


class TestFeatureEngineeringAndLeakage:
    """Tests proving absence of future data leakage and proper feature construction."""

    def test_no_target_or_future_names_in_features(self):
        """Verify no target names or future labels are present in the feature list."""
        feature_names = get_feature_column_names()
        assert len(feature_names) == 50
        for feat in feature_names:
            assert "target" not in feat.lower()
            assert "occupancy" not in feat.lower()
            assert "lead" not in feat.lower()
            assert "forward" not in feat.lower()
            assert "future" not in feat.lower()

    def test_strict_temporal_leakage_mathematical_proof(self, sample_clean_df):
        """Prove mathematically that modifying future values does not change past features."""
        # Baseline features
        features_original = build_features(sample_clean_df)
        t_index = 12  # Reference point in time: 12:12:00

        # Create modified copy where all sensor readings AFTER t_index are altered drastically
        corrupt_df = sample_clean_df.copy()
        corrupt_df.loc[t_index + 1 :, "CO2"] += 5000.0
        corrupt_df.loc[t_index + 1 :, "Temperature"] += 50.0
        corrupt_df.loc[t_index + 1 :, "Light"] += 10000.0
        corrupt_df.loc[t_index + 1 :, "Occupancy"] = 1 - corrupt_df.loc[t_index + 1 :, "Occupancy"]

        features_corrupt = build_features(corrupt_df)

        # Features at and before t_index must be strictly identical
        orig_row = features_original.iloc[t_index][FEATURE_COLUMNS].to_dict()
        corr_row = features_corrupt.iloc[t_index][FEATURE_COLUMNS].to_dict()

        for col in FEATURE_COLUMNS:
            assert orig_row[col] == pytest.approx(corr_row[col], abs=1e-7), (
                f"Feature '{col}' at t was affected by future data! Leakage detected."
            )

    def test_target_alignment_accuracy(self, sample_clean_df):
        """Verify targets are aligned at t + 10m and unmatchable tails are handled."""
        aligned = align_future_targets(sample_clean_df, horizon_minutes=10)

        # For index 0 (12:00:00), target must match ground truth at index 10 (12:10:00)
        expected_occ_10m = sample_clean_df.loc[10, "Occupancy"]
        expected_temp_10m = sample_clean_df.loc[10, "Temperature"]

        assert aligned.loc[0, TARGET_COLUMNS["occupancy"]] == expected_occ_10m
        assert aligned.loc[0, TARGET_COLUMNS["temperature"]] == pytest.approx(expected_temp_10m)

        # Final 10 rows (from index 20 onwards) should have NaN because 12:20 + 10m = 12:30 is beyond series end
        assert aligned.loc[20:, TARGET_COLUMNS["occupancy"]].isna().all()

    def test_prepare_modeling_split_boundary_exclusions(self, sample_clean_df):
        """Verify boundary exclusions: exactly 10 head rows and 10 tail rows dropped."""
        X, y_dict, stats = prepare_modeling_split(sample_clean_df, horizon_minutes=10, max_lag_minutes=10)

        # 30 total rows - 10 head (lags) - 10 tail (future target) = 10 usable rows
        assert stats["total_input_rows"] == 30
        assert stats["head_rows_dropped_for_lags"] == 10
        assert stats["tail_rows_dropped_for_horizon"] == 10
        assert stats["usable_samples"] == 10
        assert len(X) == 10
        assert len(y_dict["occupancy"]) == 10
        assert X.isna().sum().sum() == 0


class TestModelTrainingAndInference:
    """Tests for model serialization, baselines, and predictor inference."""

    def test_persistence_regressor(self, sample_clean_df):
        """Verify PersistenceRegressor correctly outputs current sensor reading."""
        reg = PersistenceRegressor(sensor_column="Temperature")
        reg.fit(sample_clean_df)
        preds = reg.predict(sample_clean_df)

        assert np.allclose(preds, sample_clean_df["Temperature"].to_numpy())

    def test_model_serialization(self, tmp_path, sample_clean_df):
        """Verify model serialization and deserialization produces identical predictions."""
        X, y_dict, _ = prepare_modeling_split(sample_clean_df)
        model = create_temperature_regressor()
        model.fit(X, y_dict["temperature"])

        model_path = tmp_path / "temp_test_model.joblib"
        joblib.dump(model, model_path)

        loaded_model = joblib.load(model_path)
        orig_preds = model.predict(X)
        loaded_preds = loaded_model.predict(X)

        assert np.allclose(orig_preds, loaded_preds)

    def test_roomiq_predictor_inference_smoke(self, tmp_path, sample_clean_df):
        """Verify RoomIQPredictor loads artifacts and generates structured forecasts."""
        X, y_dict, _ = prepare_modeling_split(sample_clean_df)

        # Train miniature models
        occ_model = create_occupancy_classifier()
        occ_model.fit(X, y_dict["occupancy"])

        temp_model = create_temperature_regressor()
        temp_model.fit(X, y_dict["temperature"])

        hum_model = create_humidity_regressor()
        hum_model.fit(X, y_dict["humidity"])

        # Save artifacts
        joblib.dump(occ_model, tmp_path / "occupancy_model.joblib")
        joblib.dump(temp_model, tmp_path / "temperature_model.joblib")
        joblib.dump(hum_model, tmp_path / "humidity_model.joblib")

        import json
        meta = {
            "prediction_horizon_minutes": 10,
            "feature_names": FEATURE_COLUMNS,
        }
        with open(tmp_path / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(meta, f)

        # Load fresh predictor instance
        predictor = RoomIQPredictor.load(tmp_path)
        assert predictor.prediction_horizon_minutes == 10

        # Test single-row prediction
        sample_row = X.iloc[0].to_dict()
        pred_single = predictor.predict(sample_row)

        assert "future_occupancy" in pred_single
        assert "occupancy_probability" in pred_single
        assert "future_temperature" in pred_single
        assert "future_humidity" in pred_single
        assert pred_single["future_occupancy"] in [0, 1]
        assert 0.0 <= pred_single["occupancy_probability"] <= 1.0

        # Test batch prediction
        pred_batch = predictor.predict(X.iloc[:5])
        assert pred_batch["sample_count"] == 5
        assert len(pred_batch["future_occupancy"]) == 5

    def test_predictor_missing_feature_raises(self, tmp_path, sample_clean_df):
        """Verify predictor raises ValueError when required feature columns are missing."""
        X, y_dict, _ = prepare_modeling_split(sample_clean_df)
        occ_model = create_occupancy_classifier()
        occ_model.fit(X, y_dict["occupancy"])

        joblib.dump(occ_model, tmp_path / "occupancy_model.joblib")
        joblib.dump(occ_model, tmp_path / "temperature_model.joblib")
        joblib.dump(occ_model, tmp_path / "humidity_model.joblib")

        import json
        with open(tmp_path / "metadata.json", "w", encoding="utf-8") as f:
            json.dump({"prediction_horizon_minutes": 10, "feature_names": FEATURE_COLUMNS}, f)

        predictor = RoomIQPredictor.load(tmp_path)
        incomplete_row = {"Temperature": 21.0, "Humidity": 30.0}

        with pytest.raises(ValueError, match="missing required features"):
            predictor.predict(incomplete_row)
