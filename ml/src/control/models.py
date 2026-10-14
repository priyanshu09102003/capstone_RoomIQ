"""Typed data models and configuration for the RoomIQ virtual appliance control engine."""

from datetime import datetime
from typing import Any, Dict, List, Optional
import math
from pydantic import BaseModel, Field, model_validator, field_validator


class ControlConfig(BaseModel):
    """Configuration parameters for RoomIQ virtual appliance control policies.

    NOTE: The default threshold values provided below are heuristic demonstration
    defaults and have not been scientifically optimized for building energy efficiency,
    comfort standards (such as ASHRAE 55), or specific room layouts.
    """

    fan_temp_on_threshold: float = Field(
        default=22.5,
        description="Forecast temperature (°C) above which the virtual fan switches ON.",
    )
    fan_temp_off_threshold: float = Field(
        default=21.5,
        description="Forecast temperature (°C) below which the virtual fan switches OFF.",
    )
    fan_min_switching_interval_seconds: int = Field(
        default=300,
        ge=0,
        description="Minimum seconds between virtual fan state switches to prevent short-cycling.",
    )
    light_lux_threshold: float = Field(
        default=250.0,
        ge=0.0,
        description="Recorded ambient light (Lux) below which lights turn ON when occupied.",
    )
    light_vacancy_delay_seconds: int = Field(
        default=300,
        ge=0,
        description="Seconds to maintain light ON after the room is predicted vacant.",
    )

    @model_validator(mode="after")
    def validate_thresholds(self) -> "ControlConfig":
        """Verify hysteresis band consistency."""
        if math.isnan(self.fan_temp_on_threshold) or math.isnan(self.fan_temp_off_threshold):
            raise ValueError("Fan temperature thresholds cannot be NaN.")
        if self.fan_temp_off_threshold >= self.fan_temp_on_threshold:
            raise ValueError(
                f"fan_temp_off_threshold ({self.fan_temp_off_threshold}) must be strictly less "
                f"than fan_temp_on_threshold ({self.fan_temp_on_threshold}) to maintain hysteresis."
            )
        return self


class SensorSnapshot(BaseModel):
    """Instantaneous sensor observation at decision time."""

    timestamp: datetime = Field(description="Observation timestamp.")
    temperature: float = Field(description="Recorded room temperature in °C.")
    humidity: float = Field(description="Recorded relative humidity in %.")
    light: float = Field(ge=0.0, description="Recorded ambient light level in Lux.")
    co2: float = Field(ge=0.0, description="Recorded carbon dioxide in ppm.")
    humidity_ratio: float = Field(ge=0.0, description="Recorded humidity ratio in kg/kg.")

    @field_validator("temperature", "humidity", "light", "co2", "humidity_ratio")
    @classmethod
    def check_non_nan(cls, v: float, info) -> float:
        if math.isnan(v):
            raise ValueError(f"Sensor field '{info.field_name}' cannot be NaN.")
        return v


class PredictionPayload(BaseModel):
    """Machine learning forecast outputs for the 10-minute horizon."""

    forecast_temperature: float = Field(description="Predicted temperature at t+10m (°C).")
    forecast_humidity: float = Field(description="Predicted humidity at t+10m (%).")
    predicted_occupancy: int = Field(description="Predicted occupancy state (0=Empty, 1=Occupied).")
    occupancy_probability: float = Field(
        ge=0.0,
        le=1.0,
        description="Model confidence probability for occupancy state.",
    )
    prediction_horizon_minutes: int = Field(default=10, description="Forecast horizon in minutes.")

    @field_validator("forecast_temperature", "forecast_humidity", "occupancy_probability")
    @classmethod
    def check_non_nan(cls, v: float, info) -> float:
        if math.isnan(v):
            raise ValueError(f"Prediction field '{info.field_name}' cannot be NaN.")
        return v

    @field_validator("predicted_occupancy")
    @classmethod
    def check_binary(cls, v: int) -> int:
        if v not in (0, 1):
            raise ValueError(f"predicted_occupancy must be 0 or 1, got: {v}")
        return v


class ApplianceState(BaseModel):
    """State tracking for RoomIQ virtual appliances (simulated actuators).

    NOTE: These represent virtual devices inside RoomIQ software, not physical appliances.
    """

    fan_on: bool = Field(default=False, description="Virtual fan active state.")
    light_on: bool = Field(default=False, description="Virtual light active state.")
    fan_last_switched_at: Optional[datetime] = Field(
        default=None, description="Timestamp of the most recent fan state toggle."
    )
    light_last_switched_at: Optional[datetime] = Field(
        default=None, description="Timestamp of the most recent light state toggle."
    )
    last_occupied_at: Optional[datetime] = Field(
        default=None, description="Timestamp when occupancy was last detected or predicted as 1."
    )


class TransitionEvent(BaseModel):
    """Structured audit event logged when a virtual appliance changes state."""

    timestamp: datetime = Field(description="Event transition timestamp.")
    device: str = Field(description="Appliance identifier ('fan' or 'light').")
    previous_state: bool = Field(description="State before transition.")
    new_state: bool = Field(description="State after transition.")
    decision_reason: str = Field(description="Human-readable decision explanation.")
    sensor_readings: Dict[str, float] = Field(description="Sensor context snapshot at decision time.")
    forecast_outputs: Dict[str, Any] = Field(description="Forecast context snapshot at decision time.")


class DecisionOutcome(BaseModel):
    """Deterministic result of a single control policy evaluation step."""

    timestamp: datetime = Field(description="Evaluation timestamp.")
    new_state: ApplianceState = Field(description="Updated virtual appliance states.")
    fan_switched: bool = Field(description="Whether the fan changed state in this step.")
    light_switched: bool = Field(description="Whether the light changed state in this step.")
    fan_reason: str = Field(description="Rationale for fan state.")
    light_reason: str = Field(description="Rationale for light state.")
    events: List[TransitionEvent] = Field(
        default_factory=list,
        description="Transition events emitted during this step (empty if no state flipped).",
    )
