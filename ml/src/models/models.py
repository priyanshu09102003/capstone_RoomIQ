"""Model definitions and baselines for RoomIQ forecasting."""

from typing import Optional
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin, ClassifierMixin
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor


class PersistenceRegressor(BaseEstimator, RegressorMixin):
    """Persistence baseline for time-series sensor forecasting.

    Predicts that future sensor value at t+horizon equals the current
    instantaneous sensor value at time t: y_hat(t+horizon) = x_sensor(t).
    """

    def __init__(self, sensor_column: str = "Temperature"):
        self.sensor_column = sensor_column
        self.feature_names_in_ = None

    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None):
        """Fit persistence baseline (stores feature names)."""
        if isinstance(X, pd.DataFrame):
            self.feature_names_in_ = list(X.columns)
            if self.sensor_column not in X.columns:
                raise ValueError(
                    f"Sensor column '{self.sensor_column}' not found in features: {X.columns.tolist()}"
                )
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict future value using current instantaneous reading."""
        if isinstance(X, pd.DataFrame):
            return X[self.sensor_column].to_numpy().astype(float)
        # If numpy array, assume first column corresponds to sensor if column not specified
        return np.asarray(X)[:, 0].astype(float)


def create_occupancy_classifier() -> RandomForestClassifier:
    """Instantiate candidate Random Forest classifier for future occupancy."""
    return RandomForestClassifier(
        n_estimators=100,
        max_depth=12,
        min_samples_split=5,
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=-1,
    )


def create_occupancy_baseline() -> DummyClassifier:
    """Instantiate majority-class baseline for occupancy classification."""
    return DummyClassifier(strategy="most_frequent")


def create_temperature_regressor() -> RandomForestRegressor:
    """Instantiate candidate Random Forest regressor for future temperature."""
    return RandomForestRegressor(
        n_estimators=100,
        max_depth=12,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )


def create_humidity_regressor() -> RandomForestRegressor:
    """Instantiate candidate Random Forest regressor for future humidity."""
    return RandomForestRegressor(
        n_estimators=100,
        max_depth=12,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )


def create_temperature_baseline() -> PersistenceRegressor:
    """Instantiate persistence baseline for temperature."""
    return PersistenceRegressor(sensor_column="Temperature")


def create_humidity_baseline() -> PersistenceRegressor:
    """Instantiate persistence baseline for humidity."""
    return PersistenceRegressor(sensor_column="Humidity")
