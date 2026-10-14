"""RoomIQ Predictor for production and smoke-test inference."""

from pathlib import Path
from typing import Any, Dict, List, Union
import json
import joblib
import numpy as np
import pandas as pd


class RoomIQPredictor:
    """Inference engine that loads trained artifacts and generates future forecasts."""

    def __init__(
        self,
        occupancy_model: Any,
        temperature_model: Any,
        humidity_model: Any,
        metadata: Dict[str, Any],
    ):
        self.occupancy_model = occupancy_model
        self.temperature_model = temperature_model
        self.humidity_model = humidity_model
        self.metadata = metadata
        self.feature_names: List[str] = metadata.get("feature_names", [])
        self.prediction_horizon_minutes: int = metadata.get("prediction_horizon_minutes", 10)

    @classmethod
    def load(cls, artifact_dir: Union[str, Path]) -> "RoomIQPredictor":
        """Load trained model artifacts and metadata from disk without retraining.

        Args:
            artifact_dir: Path to directory containing saved joblib and json files.

        Returns:
            Configured RoomIQPredictor ready for inference.

        Raises:
            FileNotFoundError: If any mandatory artifact file is missing.
        """
        dir_path = Path(artifact_dir)

        occ_path = dir_path / "occupancy_model.joblib"
        temp_path = dir_path / "temperature_model.joblib"
        hum_path = dir_path / "humidity_model.joblib"
        meta_path = dir_path / "metadata.json"

        for p in [occ_path, temp_path, hum_path, meta_path]:
            if not p.exists():
                raise FileNotFoundError(f"Missing required artifact: {p}")

        occ_model = joblib.load(occ_path)
        temp_model = joblib.load(temp_path)
        hum_model = joblib.load(hum_path)

        with open(meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        return cls(
            occupancy_model=occ_model,
            temperature_model=temp_model,
            humidity_model=hum_model,
            metadata=metadata,
        )

    def validate_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """Verify presence and order of required predictor features."""
        missing = [f for f in self.feature_names if f not in X.columns]
        if missing:
            raise ValueError(f"Input DataFrame is missing required features: {missing[:10]} (total missing: {len(missing)})")
        return X[self.feature_names]

    def predict(self, X: Union[pd.DataFrame, Dict[str, Any]]) -> Dict[str, Any]:
        """Generate forecasts for occupancy, temperature, and humidity.

        Args:
            X: Input DataFrame or dictionary containing feature values.

        Returns:
            Dictionary with predicted values and probability confidence.
        """
        if isinstance(X, dict):
            df_in = pd.DataFrame([X])
        else:
            df_in = X.copy()

        df_valid = self.validate_features(df_in)

        # 1. Occupancy predictions
        occ_pred = self.occupancy_model.predict(df_valid)
        if hasattr(self.occupancy_model, "predict_proba"):
            probs = self.occupancy_model.predict_proba(df_valid)
            if hasattr(self.occupancy_model, "classes_"):
                class_1_indices = np.where(self.occupancy_model.classes_ == 1)[0]
                if len(class_1_indices) > 0:
                    occ_prob = probs[:, class_1_indices[0]]
                else:
                    occ_prob = np.zeros(len(df_valid), dtype=float)
            else:
                occ_prob = probs[:, 1] if probs.shape[1] > 1 else probs[:, 0]
        else:
            occ_prob = occ_pred.astype(float)

        # 2. Temperature predictions
        temp_pred = self.temperature_model.predict(df_valid)

        # 3. Humidity predictions
        hum_pred = self.humidity_model.predict(df_valid)

        is_single = len(df_in) == 1

        return {
            "prediction_horizon_minutes": self.prediction_horizon_minutes,
            "future_occupancy": int(occ_pred[0]) if is_single else occ_pred.tolist(),
            "occupancy_probability": float(occ_prob[0]) if is_single else occ_prob.tolist(),
            "future_temperature": float(temp_pred[0]) if is_single else temp_pred.tolist(),
            "future_humidity": float(hum_pred[0]) if is_single else hum_pred.tolist(),
            "sample_count": len(df_in),
        }
