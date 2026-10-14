"""Data models and schemas for the RoomIQ dataset replay simulator."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.control.models import ApplianceState, ControlConfig, SensorSnapshot, TransitionEvent, PredictionPayload


class SimulationStatus(str, Enum):
    """Operational status of the replay simulator."""

    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"


class SimulationConfig(BaseModel):
    """Configuration options for simulator initialization and playback."""

    split_name: str = Field(
        default="test2",
        description="Dataset partition to replay ('test2', 'test', 'training').",
    )
    data_file: Optional[Path] = Field(
        default=None,
        description="Optional custom CSV file path to override split_name.",
    )
    start_index: int = Field(
        default=10,
        ge=0,
        description="Replay starting index (default 10 ensures full 10-minute historical lag window).",
    )
    max_steps: Optional[int] = Field(
        default=None,
        description="Maximum steps to execute before completing (None for entire file).",
    )
    playback_speed: float = Field(
        default=1.0,
        gt=0.0,
        description="Playback speed multiplier for continuous background replay (e.g. 1.0, 5.0).",
    )
    control_config: ControlConfig = Field(
        default_factory=ControlConfig,
        description="Threshold and timer settings for the automation decision engine.",
    )


class RetrospectiveComparison(BaseModel):
    """Comparison between an earlier forecast and the actual ground truth that has now arrived."""

    prediction_timestamp: datetime = Field(description="Timestamp when the forecast was issued (t).")
    target_timestamp: datetime = Field(description="Target arrival timestamp (t+10m).")
    predicted_occupancy: int = Field(description="Predicted occupancy label.")
    actual_occupancy: int = Field(description="Ground truth occupancy at arrival.")
    occupancy_correct: bool = Field(description="Whether occupancy prediction matched reality.")
    forecast_temperature: float = Field(description="Forecast temperature (°C).")
    actual_temperature: float = Field(description="Actual temperature recorded (°C).")
    temperature_error: float = Field(description="Actual - Forecast temperature (°C).")
    forecast_humidity: float = Field(description="Forecast relative humidity (%).")
    actual_humidity: float = Field(description="Actual relative humidity recorded (%).")
    humidity_error: float = Field(description="Actual - Forecast humidity (%).")


class SimulationStepResult(BaseModel):
    """Output packet emitted after each single simulation step."""

    step_index: int = Field(description="Zero-based sequence index in the replay.")
    timestamp: datetime = Field(description="Current observation timestamp.")
    system_label: str = Field(
        default="DATASET REPLAY / SIMULATION",
        description="Explicit identifier indicating synthetic replay execution.",
    )
    sensor_snapshot: SensorSnapshot = Field(description="Current instantaneous sensor readings.")
    prediction: PredictionPayload = Field(description="ML 10-minute forecast.")
    appliance_state: ApplianceState = Field(description="Updated virtual appliance states.")
    transition_events: List[TransitionEvent] = Field(
        default_factory=list,
        description="Appliance state flips triggered at this step.",
    )
    retrospective_evaluation: Optional[RetrospectiveComparison] = Field(
        default=None,
        description="Error evaluation if a past prediction matured at this step.",
    )
    future_ground_truth: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Known ground truth at t+10m from the dataset (for dashboard evaluation only).",
    )


class SimulationStateSummary(BaseModel):
    """Overall status and telemetry summary of the simulator."""

    system_label: str = Field(default="DATASET REPLAY / SIMULATION")
    status: SimulationStatus = Field(description="Current simulator lifecycle state.")
    current_index: int = Field(description="Current sequence pointer index.")
    total_records: int = Field(description="Total observations available in loaded dataset.")
    current_timestamp: Optional[datetime] = Field(default=None)
    playback_speed: float = Field(description="Speed multiplier.")
    appliance_state: ApplianceState = Field(description="Current virtual appliance states.")
    events_count: int = Field(description="Total transition events logged since reset.")
    completed: bool = Field(description="Whether end-of-dataset has been reached.")
