"""Deterministic virtual appliance decision engine for RoomIQ."""

from datetime import datetime
from typing import List, Tuple
from src.control.models import (
    ApplianceState,
    ControlConfig,
    DecisionOutcome,
    PredictionPayload,
    SensorSnapshot,
    TransitionEvent,
)


class RoomIQControlPolicy:
    """Standalone, deterministic decision engine for virtual fans and lights.

    Processes incoming sensor observations and model forecasts against configurable
    control policies with temperature hysteresis and occupancy vacancy timers.

    NOTE: This policy controls virtual software devices, not physical hardware.
    """

    def __init__(self, config: ControlConfig = None):
        self.config = config or ControlConfig()

    def evaluate_fan(
        self,
        sensors: SensorSnapshot,
        predictions: PredictionPayload,
        current_state: ApplianceState,
    ) -> Tuple[bool, bool, str]:
        """Evaluate fan state transition independently.

        Returns:
            Tuple of (new_fan_on: bool, switched: bool, reason: str)
        """
        temp = predictions.forecast_temperature
        on_thresh = self.config.fan_temp_on_threshold
        off_thresh = self.config.fan_temp_off_threshold
        min_interval = self.config.fan_min_switching_interval_seconds

        # Compute elapsed time since last fan toggle
        if current_state.fan_last_switched_at is not None:
            elapsed = (sensors.timestamp - current_state.fan_last_switched_at).total_seconds()
            if elapsed < 0:
                raise ValueError(
                    f"Observation timestamp ({sensors.timestamp}) precedes fan_last_switched_at "
                    f"({current_state.fan_last_switched_at}). Timestamps must be non-decreasing."
                )
        else:
            elapsed = float("inf")

        if not current_state.fan_on:
            # Current state: OFF
            if temp >= on_thresh:
                if elapsed < min_interval:
                    return (
                        False,
                        False,
                        f"Forecast temp ({temp:.2f}°C) >= ON threshold ({on_thresh:.2f}°C), "
                        f"but minimum switching interval ({min_interval}s) not met ({elapsed:.0f}s elapsed); remaining OFF",
                    )
                return (
                    True,
                    True,
                    f"Forecast temp ({temp:.2f}°C) >= ON threshold ({on_thresh:.2f}°C); switching ON",
                )
            return (
                False,
                False,
                f"Forecast temp ({temp:.2f}°C) < ON threshold ({on_thresh:.2f}°C); remaining OFF",
            )
        else:
            # Current state: ON
            if temp <= off_thresh:
                if elapsed < min_interval:
                    return (
                        True,
                        False,
                        f"Forecast temp ({temp:.2f}°C) <= OFF threshold ({off_thresh:.2f}°C), "
                        f"but minimum switching interval ({min_interval}s) not met ({elapsed:.0f}s elapsed); remaining ON",
                    )
                return (
                    False,
                    True,
                    f"Forecast temp ({temp:.2f}°C) <= OFF threshold ({off_thresh:.2f}°C); switching OFF",
                )
            return (
                True,
                False,
                f"Forecast temp ({temp:.2f}°C) > OFF threshold ({off_thresh:.2f}°C); maintaining ON (hysteresis band)",
            )

    def evaluate_light(
        self,
        sensors: SensorSnapshot,
        predictions: PredictionPayload,
        current_state: ApplianceState,
    ) -> Tuple[bool, bool, str, datetime]:
        """Evaluate light state transition independently.

        Returns:
            Tuple of (new_light_on: bool, switched: bool, reason: str, updated_last_occupied: datetime)
        """
        lux_thresh = self.config.light_lux_threshold
        vacancy_delay = self.config.light_vacancy_delay_seconds

        # Update last_occupied_at timestamp
        if predictions.predicted_occupancy == 1:
            updated_last_occupied = sensors.timestamp
        else:
            updated_last_occupied = current_state.last_occupied_at

        if predictions.predicted_occupancy == 1:
            # Room is predicted occupied
            if not current_state.light_on:
                if sensors.light < lux_thresh:
                    return (
                        True,
                        True,
                        f"Room predicted occupied (prob {predictions.occupancy_probability:.2f}) and "
                        f"ambient light ({sensors.light:.1f} Lux) < threshold ({lux_thresh:.1f} Lux); switching ON",
                        updated_last_occupied,
                    )
                return (
                    False,
                    False,
                    f"Room predicted occupied, but natural light ({sensors.light:.1f} Lux) >= threshold ({lux_thresh:.1f} Lux); remaining OFF",
                    updated_last_occupied,
                )
            return (
                True,
                False,
                "Room predicted occupied; maintaining light ON",
                updated_last_occupied,
            )
        else:
            # Room is predicted vacant (predicted_occupancy == 0)
            if current_state.light_on:
                if current_state.last_occupied_at is None:
                    vacant_elapsed = float("inf")
                else:
                    vacant_elapsed = (sensors.timestamp - current_state.last_occupied_at).total_seconds()
                    if vacant_elapsed < 0:
                        raise ValueError(
                            f"Observation timestamp ({sensors.timestamp}) precedes last_occupied_at "
                            f"({current_state.last_occupied_at})."
                        )

                if vacant_elapsed >= vacancy_delay:
                    return (
                        False,
                        True,
                        f"Room predicted vacant and vacancy delay ({vacancy_delay}s) expired ({vacant_elapsed:.0f}s elapsed); switching OFF",
                        updated_last_occupied,
                    )
                return (
                    True,
                    False,
                    f"Room predicted vacant, holding light ON until vacancy delay expires ({vacancy_delay}s; {vacant_elapsed:.0f}s elapsed)",
                    updated_last_occupied,
                )
            return (
                False,
                False,
                "Room predicted vacant; light remains OFF",
                updated_last_occupied,
            )

    def step(
        self,
        sensors: SensorSnapshot,
        predictions: PredictionPayload,
        current_state: ApplianceState,
    ) -> DecisionOutcome:
        """Execute a deterministic policy evaluation step.

        Args:
            sensors: Validated instantaneous sensor readings.
            predictions: Validated machine learning forecast payload.
            current_state: Current states and switch timestamps of virtual appliances.

        Returns:
            DecisionOutcome containing new states, transition rationales, and audit events.
        """
        # 1. Evaluate Fan
        fan_new, fan_switched, fan_reason = self.evaluate_fan(sensors, predictions, current_state)

        # 2. Evaluate Light
        light_new, light_switched, light_reason, new_last_occupied = self.evaluate_light(
            sensors, predictions, current_state
        )

        # 3. Formulate updated appliance state
        new_fan_switched_at = (
            sensors.timestamp if fan_switched else current_state.fan_last_switched_at
        )
        new_light_switched_at = (
            sensors.timestamp if light_switched else current_state.light_last_switched_at
        )

        new_state = ApplianceState(
            fan_on=fan_new,
            light_on=light_new,
            fan_last_switched_at=new_fan_switched_at,
            light_last_switched_at=new_light_switched_at,
            last_occupied_at=new_last_occupied,
        )

        # 4. Record transition events (only when a device flips state)
        events: List[TransitionEvent] = []

        sensor_dict = {
            "temperature": sensors.temperature,
            "humidity": sensors.humidity,
            "light": sensors.light,
            "co2": sensors.co2,
            "humidity_ratio": sensors.humidity_ratio,
        }
        forecast_dict = {
            "forecast_temperature": predictions.forecast_temperature,
            "forecast_humidity": predictions.forecast_humidity,
            "predicted_occupancy": predictions.predicted_occupancy,
            "occupancy_probability": predictions.occupancy_probability,
            "horizon_minutes": predictions.prediction_horizon_minutes,
        }

        if fan_switched:
            events.append(
                TransitionEvent(
                    timestamp=sensors.timestamp,
                    device="fan",
                    previous_state=current_state.fan_on,
                    new_state=fan_new,
                    decision_reason=fan_reason,
                    sensor_readings=sensor_dict,
                    forecast_outputs=forecast_dict,
                )
            )

        if light_switched:
            events.append(
                TransitionEvent(
                    timestamp=sensors.timestamp,
                    device="light",
                    previous_state=current_state.light_on,
                    new_state=light_new,
                    decision_reason=light_reason,
                    sensor_readings=sensor_dict,
                    forecast_outputs=forecast_dict,
                )
            )

        return DecisionOutcome(
            timestamp=sensors.timestamp,
            new_state=new_state,
            fan_switched=fan_switched,
            light_switched=light_switched,
            fan_reason=fan_reason,
            light_reason=light_reason,
            events=events,
        )
