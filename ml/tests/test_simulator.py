"""Unit tests for the RoomIQ dataset replay simulation engine."""

from datetime import datetime, timedelta
from pathlib import Path
import pytest

from src.simulation.models import SimulationConfig, SimulationStatus, SimulationStepResult
from src.simulation.simulator import RoomIQSimulator


@pytest.fixture
def base_artifact_dir() -> Path:
    """Path to the verified saved ML model artifacts."""
    return Path(__file__).resolve().parent.parent / "artifacts"


@pytest.fixture
def base_data_dir() -> Path:
    """Path to the processed datasets."""
    return Path(__file__).resolve().parent.parent / "data" / "processed"


class TestRoomIQSimulator:
    """Tests for playback controls, step execution, determinism, and safety."""

    def test_simulator_initialization(self, base_data_dir, base_artifact_dir):
        """Simulator must initialize with IDLE status and correct dataset metadata."""
        config = SimulationConfig(split_name="test2", start_index=10)
        sim = RoomIQSimulator(config=config, data_dir=base_data_dir, artifact_dir=base_artifact_dir)

        summary = sim.get_summary()
        assert summary.system_label == "DATASET REPLAY / SIMULATION"
        assert summary.status == SimulationStatus.IDLE
        assert summary.current_index == 10
        assert summary.total_records == 9752
        assert summary.events_count == 0
        assert summary.completed is False
        assert summary.appliance_state.fan_on is False
        assert summary.appliance_state.light_on is False

    def test_single_step_execution(self, base_data_dir, base_artifact_dir):
        """Single-step operation must advance index and produce validated step packet."""
        config = SimulationConfig(split_name="test2", start_index=10)
        sim = RoomIQSimulator(config=config, data_dir=base_data_dir, artifact_dir=base_artifact_dir)

        result: SimulationStepResult = sim.step()

        assert result.step_index == 10
        assert result.system_label == "DATASET REPLAY / SIMULATION"
        assert isinstance(result.timestamp, datetime)
        # Sensor snapshot valid
        assert result.sensor_snapshot.temperature > 0
        assert result.sensor_snapshot.co2 > 0
        # Prediction valid
        assert result.prediction.predicted_occupancy in [0, 1]
        assert 0.0 <= result.prediction.occupancy_probability <= 1.0
        assert result.prediction.forecast_temperature > 0
        assert result.prediction.prediction_horizon_minutes == 10
        # Pointer advanced
        assert sim.current_index == 11
        assert len(sim.history_steps) == 1

    def test_feature_isolation_no_future_leakage(self, base_data_dir, base_artifact_dir, tmp_path):
        """Feature inputs at step k must be strictly identical even if future rows are truncated."""
        # Run 1: Full dataset step at index 15
        config_full = SimulationConfig(split_name="test2", start_index=15)
        sim_full = RoomIQSimulator(config=config_full, data_dir=base_data_dir, artifact_dir=base_artifact_dir)
        step_full = sim_full.step()

        # Run 2: Dataset truncated exactly at row 15 (zero future rows exist)
        truncated_csv = tmp_path / "truncated.csv"
        df_trunc = sim_full.dataset_df.iloc[:16].copy()
        df_trunc.to_csv(truncated_csv, index=False)

        config_trunc = SimulationConfig(data_file=truncated_csv, start_index=15)
        sim_trunc = RoomIQSimulator(config=config_trunc, artifact_dir=base_artifact_dir)
        step_trunc = sim_trunc.step()

        # Predictions and appliance states must be 100% identical
        assert step_full.prediction.predicted_occupancy == step_trunc.prediction.predicted_occupancy
        assert step_full.prediction.forecast_temperature == pytest.approx(step_trunc.prediction.forecast_temperature)
        assert step_full.prediction.forecast_humidity == pytest.approx(step_trunc.prediction.forecast_humidity)
        assert step_full.appliance_state.fan_on == step_trunc.appliance_state.fan_on
        assert step_full.appliance_state.light_on == step_trunc.appliance_state.light_on

    def test_playback_lifecycle_start_pause_resume(self, base_data_dir, base_artifact_dir):
        """Lifecycle operations must properly manage simulator state machine."""
        config = SimulationConfig(split_name="test2", start_index=10)
        sim = RoomIQSimulator(config=config, data_dir=base_data_dir, artifact_dir=base_artifact_dir)

        assert sim.status == SimulationStatus.IDLE
        sim.start()
        assert sim.status == SimulationStatus.RUNNING

        sim.pause()
        assert sim.status == SimulationStatus.PAUSED

        sim.resume()
        assert sim.status == SimulationStatus.RUNNING

        sim.reset()
        assert sim.status == SimulationStatus.IDLE

    def test_reset_restores_identical_initial_state(self, base_data_dir, base_artifact_dir):
        """Reset operation must return the simulator to its exact initial configuration."""
        config = SimulationConfig(split_name="test2", start_index=10)
        sim = RoomIQSimulator(config=config, data_dir=base_data_dir, artifact_dir=base_artifact_dir)

        # Advance 5 steps
        for _ in range(5):
            sim.step()

        assert sim.current_index == 15
        assert len(sim.history_steps) == 5

        # Reset
        sim.reset()

        assert sim.status == SimulationStatus.IDLE
        assert sim.current_index == 10
        assert sim.appliance_state.fan_on is False
        assert sim.appliance_state.light_on is False
        assert len(sim.event_log) == 0
        assert len(sim.history_steps) == 0
        assert len(sim.pending_predictions) == 0

    def test_determinism_across_replays(self, base_data_dir, base_artifact_dir):
        """Replaying the exact same segment after reset must produce strictly identical outputs."""
        config = SimulationConfig(split_name="test2", start_index=10)
        sim = RoomIQSimulator(config=config, data_dir=base_data_dir, artifact_dir=base_artifact_dir)

        # First run: 10 steps
        run1_results = [sim.step() for _ in range(10)]

        # Reset
        sim.reset()

        # Second run: 10 steps
        run2_results = [sim.step() for _ in range(10)]

        assert len(run1_results) == len(run2_results) == 10

        for r1, r2 in zip(run1_results, run2_results):
            assert r1.step_index == r2.step_index
            assert r1.timestamp == r2.timestamp
            assert r1.prediction.predicted_occupancy == r2.prediction.predicted_occupancy
            assert r1.prediction.forecast_temperature == pytest.approx(r2.prediction.forecast_temperature)
            assert r1.prediction.forecast_humidity == pytest.approx(r2.prediction.forecast_humidity)
            assert r1.appliance_state.fan_on == r2.appliance_state.fan_on
            assert r1.appliance_state.light_on == r2.appliance_state.light_on
            assert len(r1.transition_events) == len(r2.transition_events)

    def test_end_of_data_handling(self, base_data_dir, base_artifact_dir):
        """Simulator must transition to COMPLETED upon exhaustion and reject further steps."""
        config = SimulationConfig(split_name="test2", start_index=10, max_steps=3)
        sim = RoomIQSimulator(config=config, data_dir=base_data_dir, artifact_dir=base_artifact_dir)

        # Total available is start_index (10) + max_steps (3) = 13 records
        s1 = sim.step()  # index 10 -> 11
        s2 = sim.step()  # index 11 -> 12
        s3 = sim.step()  # index 12 -> 13 (end of data)

        assert sim.current_index == 13
        assert sim.status == SimulationStatus.COMPLETED

        # Attempting an additional step must raise StopIteration
        with pytest.raises(StopIteration, match="End of simulation dataset reached"):
            sim.step()

        # Attempting start on completed must raise RuntimeError
        with pytest.raises(RuntimeError, match="Cannot start a completed simulation"):
            sim.start()

    def test_retrospective_evaluation(self, base_data_dir, base_artifact_dir):
        """Predictions made at t must be paired with actual ground truth arriving at t+10m."""
        config = SimulationConfig(split_name="test2", start_index=10)
        sim = RoomIQSimulator(config=config, data_dir=base_data_dir, artifact_dir=base_artifact_dir)

        # Run 12 steps (from index 10 to index 21)
        steps = [sim.step() for _ in range(12)]

        # Steps 0-9 (index 10-19) do not have matured predictions yet
        # Step 10 (index 20) matches prediction issued at index 10 (10 minutes earlier)
        step_eval = steps[10]
        assert step_eval.retrospective_evaluation is not None
        retro = step_eval.retrospective_evaluation

        assert retro.target_timestamp == step_eval.timestamp
        assert retro.actual_occupancy in [0, 1]
        assert retro.predicted_occupancy in [0, 1]
        assert isinstance(retro.occupancy_correct, bool)
        assert isinstance(retro.temperature_error, float)
        assert isinstance(retro.humidity_error, float)

    def test_future_ground_truth_held_separately(self, base_data_dir, base_artifact_dir):
        """Future ground truth must only be exposed in metadata, never inside sensor snapshot."""
        config = SimulationConfig(split_name="test2", start_index=10)
        sim = RoomIQSimulator(config=config, data_dir=base_data_dir, artifact_dir=base_artifact_dir)

        step = sim.step()

        # future_ground_truth exists for retrospective display
        assert step.future_ground_truth is not None
        assert "target_occupancy" in step.future_ground_truth
        assert "target_temperature" in step.future_ground_truth

        # Ensure future ground truth is not inside the sensor snapshot or prediction inputs
        sensor_dict = step.sensor_snapshot.model_dump()
        assert "target_occupancy" not in sensor_dict
        assert "future_temperature" not in sensor_dict

    def test_missing_artifacts_raises_file_not_found(self, base_data_dir, tmp_path):
        """Initializing with non-existent artifacts directory must fail fast."""
        empty_dir = tmp_path / "non_existent_artifacts"
        with pytest.raises(FileNotFoundError, match="Artifact directory not found"):
            RoomIQSimulator(data_dir=base_data_dir, artifact_dir=empty_dir)
