"""Unit tests for the RoomIQ virtual appliance automation decision engine."""

from datetime import datetime, timedelta
import pytest
from src.control.models import (
    ApplianceState,
    ControlConfig,
    PredictionPayload,
    SensorSnapshot,
)
from src.control.policy import RoomIQControlPolicy


@pytest.fixture
def default_config() -> ControlConfig:
    """Fixture providing standardized demonstration control configuration."""
    return ControlConfig(
        fan_temp_on_threshold=22.5,
        fan_temp_off_threshold=21.5,
        fan_min_switching_interval_seconds=300,  # 5 minutes
        light_lux_threshold=250.0,
        light_vacancy_delay_seconds=300,  # 5 minutes
    )


@pytest.fixture
def base_sensor() -> SensorSnapshot:
    """Fixture providing neutral sensor reading."""
    return SensorSnapshot(
        timestamp=datetime(2026, 10, 13, 10, 0, 0),
        temperature=21.0,
        humidity=30.0,
        light=100.0,
        co2=600.0,
        humidity_ratio=0.004,
    )


@pytest.fixture
def base_prediction() -> PredictionPayload:
    """Fixture providing neutral prediction payload."""
    return PredictionPayload(
        forecast_temperature=21.0,
        forecast_humidity=30.0,
        predicted_occupancy=0,
        occupancy_probability=0.1,
        prediction_horizon_minutes=10,
    )


class TestFanControlPolicy:
    """Tests for fan hysteresis, thresholds, and switching intervals."""

    def test_fan_remains_off_below_threshold(self, default_config, base_sensor, base_prediction):
        """Fan must remain OFF when forecast temperature is strictly below the ON threshold."""
        policy = RoomIQControlPolicy(default_config)
        state = ApplianceState(fan_on=False)
        pred = base_prediction.model_copy(update={"forecast_temperature": 22.0})

        outcome = policy.step(base_sensor, pred, state)

        assert outcome.new_state.fan_on is False
        assert outcome.fan_switched is False
        assert len(outcome.events) == 0
        assert "remaining OFF" in outcome.fan_reason

    def test_fan_switches_on_when_upper_threshold_crossed(self, default_config, base_sensor, base_prediction):
        """Fan must switch ON when forecast temperature reaches or exceeds the upper threshold."""
        policy = RoomIQControlPolicy(default_config)
        state = ApplianceState(fan_on=False)
        pred = base_prediction.model_copy(update={"forecast_temperature": 22.6})

        outcome = policy.step(base_sensor, pred, state)

        assert outcome.new_state.fan_on is True
        assert outcome.fan_switched is True
        assert outcome.new_state.fan_last_switched_at == base_sensor.timestamp
        assert len(outcome.events) == 1
        assert outcome.events[0].device == "fan"
        assert outcome.events[0].previous_state is False
        assert outcome.events[0].new_state is True
        assert "switching ON" in outcome.fan_reason

    def test_fan_remains_on_between_thresholds_hysteresis(self, default_config, base_sensor, base_prediction):
        """Fan must maintain ON state inside the hysteresis band (21.5°C < T < 22.5°C)."""
        policy = RoomIQControlPolicy(default_config)
        state = ApplianceState(
            fan_on=True,
            fan_last_switched_at=base_sensor.timestamp - timedelta(minutes=10),
        )
        # Inside hysteresis band: 22.0°C is between 21.5 and 22.5
        pred = base_prediction.model_copy(update={"forecast_temperature": 22.0})

        outcome = policy.step(base_sensor, pred, state)

        assert outcome.new_state.fan_on is True
        assert outcome.fan_switched is False
        assert len(outcome.events) == 0
        assert "hysteresis band" in outcome.fan_reason

    def test_fan_switches_off_below_lower_threshold(self, default_config, base_sensor, base_prediction):
        """Fan must switch OFF when forecast temperature drops to or below the lower threshold."""
        policy = RoomIQControlPolicy(default_config)
        state = ApplianceState(
            fan_on=True,
            fan_last_switched_at=base_sensor.timestamp - timedelta(minutes=10),
        )
        pred = base_prediction.model_copy(update={"forecast_temperature": 21.4})

        outcome = policy.step(base_sensor, pred, state)

        assert outcome.new_state.fan_on is False
        assert outcome.fan_switched is True
        assert outcome.new_state.fan_last_switched_at == base_sensor.timestamp
        assert len(outcome.events) == 1
        assert outcome.events[0].device == "fan"
        assert outcome.events[0].previous_state is True
        assert outcome.events[0].new_state is False
        assert "switching OFF" in outcome.fan_reason

    def test_fan_minimum_switching_interval_respected(self, default_config, base_sensor, base_prediction):
        """Fan must block state switching if minimum cycle interval has not elapsed."""
        policy = RoomIQControlPolicy(default_config)
        t0 = base_sensor.timestamp
        # Fan just switched ON 60 seconds ago (interval is 300s)
        state = ApplianceState(fan_on=True, fan_last_switched_at=t0 - timedelta(seconds=60))

        # Temperature suddenly crashes below OFF threshold
        pred = base_prediction.model_copy(update={"forecast_temperature": 20.0})
        outcome = policy.step(base_sensor, pred, state)

        # Must be blocked from turning OFF
        assert outcome.new_state.fan_on is True
        assert outcome.fan_switched is False
        assert "minimum switching interval (300s) not met" in outcome.fan_reason
        assert len(outcome.events) == 0

        # Now advance time past 300s (e.g., 301 seconds)
        t_after = t0 + timedelta(seconds=241)  # 60 + 241 = 301 seconds from last switch
        sensor_after = base_sensor.model_copy(update={"timestamp": t_after})
        outcome_after = policy.step(sensor_after, pred, state)

        assert outcome_after.new_state.fan_on is False
        assert outcome_after.fan_switched is True
        assert len(outcome_after.events) == 1


class TestLightControlPolicy:
    """Tests for occupancy-driven lighting and vacancy delay timers."""

    def test_light_switches_on_when_occupied_and_dark(self, default_config, base_sensor, base_prediction):
        """Light must switch ON when room is occupied and recorded ambient light is below threshold."""
        policy = RoomIQControlPolicy(default_config)
        state = ApplianceState(light_on=False)

        sensor = base_sensor.model_copy(update={"light": 120.0})  # < 250 Lux threshold
        pred = base_prediction.model_copy(update={"predicted_occupancy": 1, "occupancy_probability": 0.95})

        outcome = policy.step(sensor, pred, state)

        assert outcome.new_state.light_on is True
        assert outcome.light_switched is True
        assert outcome.new_state.last_occupied_at == sensor.timestamp
        assert len(outcome.events) == 1
        assert outcome.events[0].device == "light"
        assert outcome.events[0].previous_state is False
        assert outcome.events[0].new_state is True
        assert "switching ON" in outcome.light_reason

    def test_light_remains_off_when_occupied_and_bright(self, default_config, base_sensor, base_prediction):
        """Light must remain OFF if natural daylight exceeds threshold, even if occupied."""
        policy = RoomIQControlPolicy(default_config)
        state = ApplianceState(light_on=False)

        sensor = base_sensor.model_copy(update={"light": 450.0})  # >= 250 Lux
        pred = base_prediction.model_copy(update={"predicted_occupancy": 1, "occupancy_probability": 0.92})

        outcome = policy.step(sensor, pred, state)

        assert outcome.new_state.light_on is False
        assert outcome.light_switched is False
        assert outcome.new_state.last_occupied_at == sensor.timestamp
        assert len(outcome.events) == 0
        assert "remaining OFF" in outcome.light_reason

    def test_light_does_not_switch_off_before_vacancy_delay(self, default_config, base_sensor, base_prediction):
        """Light must stay ON during initial vacancy while vacancy delay is unexpired."""
        policy = RoomIQControlPolicy(default_config)
        t_now = base_sensor.timestamp
        # Room was occupied 120 seconds ago (vacancy delay is 300s)
        state = ApplianceState(
            light_on=True,
            last_occupied_at=t_now - timedelta(seconds=120),
            light_last_switched_at=t_now - timedelta(minutes=10),
        )

        pred = base_prediction.model_copy(update={"predicted_occupancy": 0, "occupancy_probability": 0.05})
        outcome = policy.step(base_sensor, pred, state)

        assert outcome.new_state.light_on is True
        assert outcome.light_switched is False
        assert len(outcome.events) == 0
        assert "holding light ON until vacancy delay expires" in outcome.light_reason

    def test_light_switches_off_after_vacancy_delay_expires(self, default_config, base_sensor, base_prediction):
        """Light must switch OFF once vacancy duration reaches or exceeds vacancy delay."""
        policy = RoomIQControlPolicy(default_config)
        t_now = base_sensor.timestamp
        # Room was occupied 305 seconds ago (vacancy delay is 300s)
        state = ApplianceState(
            light_on=True,
            last_occupied_at=t_now - timedelta(seconds=305),
            light_last_switched_at=t_now - timedelta(minutes=10),
        )

        pred = base_prediction.model_copy(update={"predicted_occupancy": 0, "occupancy_probability": 0.02})
        outcome = policy.step(base_sensor, pred, state)

        assert outcome.new_state.light_on is False
        assert outcome.light_switched is True
        assert outcome.new_state.light_last_switched_at == t_now
        assert len(outcome.events) == 1
        assert outcome.events[0].device == "light"
        assert outcome.events[0].previous_state is True
        assert outcome.events[0].new_state is False
        assert "switching OFF" in outcome.light_reason


class TestIndependenceAndDeterminism:
    """Tests proving device independence, determinism, and safety validation."""

    def test_fan_and_light_states_are_independent(self, default_config, base_sensor, base_prediction):
        """Fan triggering conditions must not modify light state, and vice versa."""
        policy = RoomIQControlPolicy(default_config)

        # High temperature (triggers fan ON) with dark occupied room (triggers light ON)
        sensor = base_sensor.model_copy(update={"light": 50.0})
        pred = base_prediction.model_copy(
            update={"forecast_temperature": 23.5, "predicted_occupancy": 1, "occupancy_probability": 0.9}
        )
        state = ApplianceState(fan_on=False, light_on=False)

        outcome = policy.step(sensor, pred, state)

        assert outcome.new_state.fan_on is True
        assert outcome.new_state.light_on is True
        assert len(outcome.events) == 2

    def test_determinism_identical_inputs_identical_outputs(self, default_config, base_sensor, base_prediction):
        """Policy must be strictly deterministic: identical inputs yield identical outputs."""
        policy = RoomIQControlPolicy(default_config)
        state = ApplianceState(
            fan_on=False,
            light_on=True,
            last_occupied_at=base_sensor.timestamp - timedelta(seconds=100),
        )

        results = [policy.step(base_sensor, base_prediction, state) for _ in range(10)]

        for res in results[1:]:
            assert res.new_state.model_dump() == results[0].new_state.model_dump()
            assert res.fan_switched == results[0].fan_switched
            assert res.light_switched == results[0].light_switched
            assert res.fan_reason == results[0].fan_reason
            assert res.light_reason == results[0].light_reason
            assert len(res.events) == len(results[0].events)

    def test_invalid_thresholds_raise_validation_error(self):
        """Config must reject invalid hysteresis bounds where OFF >= ON."""
        with pytest.raises(ValueError, match="must be strictly less than fan_temp_on_threshold"):
            ControlConfig(fan_temp_on_threshold=21.0, fan_temp_off_threshold=22.0)

        with pytest.raises(ValueError, match="must be strictly less than fan_temp_on_threshold"):
            ControlConfig(fan_temp_on_threshold=22.0, fan_temp_off_threshold=22.0)

    def test_invalid_sensor_inputs_raise_validation_error(self, base_sensor):
        """Sensor snapshot must reject negative physical values and NaNs."""
        with pytest.raises(ValueError):
            SensorSnapshot(
                timestamp=base_sensor.timestamp,
                temperature=21.0,
                humidity=30.0,
                light=-10.0,
                co2=600.0,
                humidity_ratio=0.004,
            )

        with pytest.raises(ValueError, match="cannot be NaN"):
            SensorSnapshot(
                timestamp=base_sensor.timestamp,
                temperature=float("nan"),
                humidity=30.0,
                light=100.0,
                co2=600.0,
                humidity_ratio=0.004,
            )

    def test_invalid_prediction_inputs_raise_validation_error(self, base_prediction):
        """Prediction payload must reject invalid non-binary occupancy and NaNs."""
        with pytest.raises(ValueError, match="predicted_occupancy must be 0 or 1"):
            PredictionPayload(
                forecast_temperature=21.0,
                forecast_humidity=30.0,
                predicted_occupancy=2,
                occupancy_probability=0.1,
            )

        with pytest.raises(ValueError, match="cannot be NaN"):
            PredictionPayload(
                forecast_temperature=float("nan"),
                forecast_humidity=30.0,
                predicted_occupancy=0,
                occupancy_probability=0.1,
            )

    def test_events_recorded_only_on_actual_state_transitions(self, default_config, base_sensor, base_prediction):
        """Events array must be strictly empty when no device toggles state."""
        policy = RoomIQControlPolicy(default_config)
        state = ApplianceState(fan_on=False, light_on=False)
        # Neutral conditions that keep both OFF
        outcome = policy.step(base_sensor, base_prediction, state)

        assert outcome.fan_switched is False
        assert outcome.light_switched is False
        assert outcome.events == []
