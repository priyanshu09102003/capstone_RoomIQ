"""Typed request and response schemas for the RoomIQ REST API."""

from datetime import datetime
import math
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

from src.control.models import ControlConfig, TransitionEvent
from src.simulation.models import ApplianceState, SimulationStatus, SimulationStepResult


class HealthResponse(BaseModel):
    """Health status separating API availability from model and data readiness."""

    system_label: str = Field(default="DATASET REPLAY / SIMULATION")
    status: str = Field(description="'healthy' when API and models are ready, 'degraded' otherwise.")
    api_status: str = Field(default="online", description="HTTP service lifecycle state.")
    models_ready: bool = Field(description="True if all model artifacts are loaded in memory.")
    data_ready: bool = Field(description="True if processed replay dataset is available.")
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = Field(default="1.0.0")
    details: Dict[str, Any] = Field(default_factory=dict)


class PredictRequest(BaseModel):
    """Input payload for 10-minute ML model inference.

    Accepts either an explicit `features` mapping or flat feature key-value pairs.
    """

    features: Dict[str, float] = Field(
        description="Dictionary mapping required feature column names to numeric float values."
    )

    @model_validator(mode="before")
    @classmethod
    def extract_features(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "features" in data and isinstance(data["features"], dict):
                return data
            # Allow flat feature dictionary directly in request body
            return {"features": data}
        return data

    @field_validator("features")
    @classmethod
    def validate_numeric_features(cls, v: Dict[str, float]) -> Dict[str, float]:
        if not v:
            raise ValueError("Feature dictionary cannot be empty.")
        for col, val in v.items():
            if val is None or math.isnan(val) or math.isinf(val):
                raise ValueError(f"Feature '{col}' contains invalid value: {val}. Must be finite numeric.")
        return v


class PredictResponse(BaseModel):
    """Model forecast results for occupancy, temperature, and humidity."""

    system_label: str = Field(default="DATASET REPLAY / SIMULATION")
    prediction_horizon_minutes: int = Field(default=10)
    future_occupancy: int = Field(description="Predicted occupancy label (0=Vacant, 1=Occupied).")
    occupancy_probability: float = Field(description="Model probability score for occupancy.")
    future_temperature: float = Field(description="Forecast temperature (°C) at t+10m.")
    future_humidity: float = Field(description="Forecast relative humidity (%) at t+10m.")
    timestamp: datetime = Field(default_factory=datetime.now)


class SimulationActionResponse(BaseModel):
    """Standard response for simulator control operations (start, pause, resume, reset)."""

    system_label: str = Field(default="DATASET REPLAY / SIMULATION")
    status: SimulationStatus = Field(description="Updated simulation lifecycle state.")
    message: str = Field(description="Human-readable status notification.")
    current_index: int = Field(description="Current replay pointer index.")
    timestamp: datetime = Field(default_factory=datetime.now)


class ConfigUpdateRequest(BaseModel):
    """Dynamic configuration updates for control policy and simulation playback."""

    fan_temp_on_threshold: Optional[float] = Field(
        default=None, description="Forecast temperature (°C) above which fan turns ON."
    )
    fan_temp_off_threshold: Optional[float] = Field(
        default=None, description="Forecast temperature (°C) below which fan turns OFF."
    )
    fan_min_switching_interval_seconds: Optional[int] = Field(
        default=None, ge=0, description="Minimum seconds between fan state toggles."
    )
    light_lux_threshold: Optional[float] = Field(
        default=None, ge=0.0, description="Recorded ambient light (Lux) threshold for light ON."
    )
    light_vacancy_delay_seconds: Optional[int] = Field(
        default=None, ge=0, description="Vacancy delay hold timer in seconds."
    )
    playback_speed: Optional[float] = Field(
        default=None, gt=0.0, description="Simulation playback speed multiplier."
    )

    @field_validator("fan_temp_on_threshold", "fan_temp_off_threshold", "light_lux_threshold", "playback_speed")
    @classmethod
    def check_non_nan(cls, v: Optional[float], info) -> Optional[float]:
        if v is not None and (math.isnan(v) or math.isinf(v)):
            raise ValueError(f"Field '{info.field_name}' must be a finite number.")
        return v


class FullConfigResponse(BaseModel):
    """Current effective control thresholds and simulation parameters."""

    system_label: str = Field(default="DATASET REPLAY / SIMULATION")
    control_config: ControlConfig
    playback_speed: float
    split_name: str
    start_index: int


class EventsResponse(BaseModel):
    """Virtual appliance state transition audit history."""

    system_label: str = Field(default="DATASET REPLAY / SIMULATION")
    events: List[TransitionEvent]
    total_count: int


class ModelsMetadataResponse(BaseModel):
    """Trained model inventory, feature schema, and dataset statistics."""

    system_label: str = Field(default="DATASET REPLAY / SIMULATION")
    prediction_horizon_minutes: int
    features: List[str]
    total_features: int
    training_timestamp: Optional[str] = None
    sample_counts: Optional[Dict[str, Any]] = None
    date_ranges: Optional[Dict[str, Any]] = None


class MetricsResponse(BaseModel):
    """Detailed model validation and test evaluation metrics."""

    system_label: str = Field(default="DATASET REPLAY / SIMULATION")
    training_timestamp: Optional[str] = None
    validation_metrics: Dict[str, Any]
    test1_metrics: Dict[str, Any]
    test2_metrics: Dict[str, Any]
