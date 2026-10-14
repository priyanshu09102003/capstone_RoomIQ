"""Deterministic dataset replay simulation engine for RoomIQ."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np

from src.control.models import ApplianceState, ControlConfig, SensorSnapshot, TransitionEvent, PredictionPayload
from src.control.policy import RoomIQControlPolicy
from src.features.features import build_features, FEATURE_COLUMNS
from src.models.predictor import RoomIQPredictor
from src.simulation.models import (
    RetrospectiveComparison,
    SimulationConfig,
    SimulationStateSummary,
    SimulationStatus,
    SimulationStepResult,
)


class RoomIQSimulator:
    """Deterministic time-series dataset replay simulator for RoomIQ.

    Replays cleaned historical sensor sequences chronologically, constructs non-leaking
    feature windows dynamically, generates forecasts via RoomIQPredictor, and drives
    virtual appliance decisions via RoomIQControlPolicy.

    SYSTEM CLASSIFICATION: DATASET REPLAY / SIMULATION
    NOTE: All managed devices (fan and light) are virtual software models, not physical devices.
    """

    SYSTEM_LABEL: str = "DATASET REPLAY / SIMULATION"

    def __init__(
        self,
        config: Optional[SimulationConfig] = None,
        data_dir: Optional[Path] = None,
        artifact_dir: Optional[Path] = None,
    ):
        self.config = config or SimulationConfig()

        # Resolve directories
        base_dir = Path(__file__).resolve().parent.parent.parent
        self.data_dir = Path(data_dir) if data_dir else (base_dir / "data" / "processed")
        self.artifact_dir = Path(artifact_dir) if artifact_dir else (base_dir / "artifacts")

        # Verify artifacts exist
        if not self.artifact_dir.exists():
            raise FileNotFoundError(f"Artifact directory not found: {self.artifact_dir}")

        # Initialize predictor and control policy
        self.predictor = RoomIQPredictor.load(self.artifact_dir)
        self.policy = RoomIQControlPolicy(self.config.control_config)

        # Load dataset
        self.dataset_df = self._load_dataset()
        self.total_records = len(self.dataset_df)

        if self.config.start_index >= self.total_records:
            raise ValueError(
                f"start_index ({self.config.start_index}) exceeds total records ({self.total_records})."
            )

        # State tracking
        self.status = SimulationStatus.IDLE
        self.current_index = self.config.start_index
        self.appliance_state = ApplianceState()
        self.event_log: List[TransitionEvent] = []
        self.pending_predictions: Dict[str, Dict[str, Any]] = {}
        self.history_steps: List[SimulationStepResult] = []

    def _load_dataset(self) -> pd.DataFrame:
        """Load and validate chronological dataset partition."""
        if self.config.data_file:
            path = Path(self.config.data_file)
        else:
            file_map = {
                "test2": "test2_clean.csv",
                "test": "test_clean.csv",
                "training": "training_clean.csv",
            }
            file_name = file_map.get(self.config.split_name)
            if not file_name:
                raise ValueError(f"Unknown split_name '{self.config.split_name}'. Expected one of {list(file_map.keys())}")
            path = self.data_dir / file_name

        if not path.exists():
            raise FileNotFoundError(f"Simulation dataset file not found: {path}")

        df = pd.read_csv(path)
        required_cols = ["date", "Temperature", "Humidity", "Light", "CO2", "HumidityRatio", "Occupancy"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(f"Dataset {path} missing required columns: {missing}")

        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)

        if self.config.max_steps is not None:
            max_rows = self.config.start_index + self.config.max_steps
            df = df.iloc[:max_rows].copy().reset_index(drop=True)

        return df

    def get_summary(self) -> SimulationStateSummary:
        """Retrieve current telemetry snapshot and status."""
        current_ts = (
            self.dataset_df.loc[self.current_index, "date"]
            if self.current_index < self.total_records
            else self.dataset_df.iloc[-1]["date"]
        )
        return SimulationStateSummary(
            system_label=self.SYSTEM_LABEL,
            status=self.status,
            current_index=self.current_index,
            total_records=self.total_records,
            current_timestamp=current_ts,
            playback_speed=self.config.playback_speed,
            appliance_state=self.appliance_state,
            events_count=len(self.event_log),
            completed=self.status == SimulationStatus.COMPLETED,
        )

    def start(self):
        """Start or begin simulation replay."""
        if self.status == SimulationStatus.COMPLETED:
            raise RuntimeError("Cannot start a completed simulation. Call reset() first.")
        self.status = SimulationStatus.RUNNING

    def pause(self):
        """Pause running replay."""
        if self.status == SimulationStatus.RUNNING:
            self.status = SimulationStatus.PAUSED

    def resume(self):
        """Resume paused replay."""
        if self.status == SimulationStatus.PAUSED:
            self.status = SimulationStatus.RUNNING

    def reset(self):
        """Reset replay pointer and restore identical initial state for reproducible replays."""
        self.status = SimulationStatus.IDLE
        self.current_index = self.config.start_index
        self.appliance_state = ApplianceState()
        self.event_log = []
        self.pending_predictions = {}
        self.history_steps = []

    def set_speed(self, speed: float):
        """Configure replay speed multiplier."""
        if speed <= 0:
            raise ValueError("playback_speed must be positive.")
        self.config.playback_speed = float(speed)

    def step(self) -> SimulationStepResult:
        """Execute exactly one deterministic simulation step.

        Steps forward chronologically:
        1. Reads current sensor record at current_index.
        2. Evaluates retrospective accuracy of any past prediction targeting this timestamp.
        3. Constructs non-leaking feature vector using strictly past observations (<= current_index).
        4. Generates 10-minute forecasts using RoomIQPredictor.
        5. Evaluates RoomIQControlPolicy to actuate virtual appliances.
        6. Extracts future ground truth (if within bounds) strictly for retrospective dashboard display.
        7. Advances replay pointer.

        Returns:
            SimulationStepResult packet.

        Raises:
            StopIteration: If the replay has reached the end of the dataset.
        """
        if self.current_index >= self.total_records:
            self.status = SimulationStatus.COMPLETED
            raise StopIteration("End of simulation dataset reached.")

        curr_row = self.dataset_df.iloc[self.current_index]
        curr_timestamp: datetime = curr_row["date"]

        # 1. Formulate current instantaneous sensor snapshot
        sensors = SensorSnapshot(
            timestamp=curr_timestamp,
            temperature=float(curr_row["Temperature"]),
            humidity=float(curr_row["Humidity"]),
            light=float(curr_row["Light"]),
            co2=float(curr_row["CO2"]),
            humidity_ratio=float(curr_row["HumidityRatio"]),
        )

        # 2. Check for matured retrospective predictions (issued ~10m ago targeting curr_timestamp)
        retro_eval: Optional[RetrospectiveComparison] = None
        ts_key = curr_timestamp.isoformat()

        # Find any matching pending prediction within +/- 15 seconds tolerance
        matched_target_key = None
        for target_iso, pred_record in list(self.pending_predictions.items()):
            target_dt = datetime.fromisoformat(target_iso)
            if abs((curr_timestamp - target_dt).total_seconds()) <= 15:
                pred = pred_record["prediction"]
                pred_ts = pred_record["timestamp"]
                actual_occ = int(curr_row["Occupancy"])
                actual_t = float(curr_row["Temperature"])
                actual_h = float(curr_row["Humidity"])

                retro_eval = RetrospectiveComparison(
                    prediction_timestamp=pred_ts,
                    target_timestamp=curr_timestamp,
                    predicted_occupancy=pred.predicted_occupancy,
                    actual_occupancy=actual_occ,
                    occupancy_correct=(pred.predicted_occupancy == actual_occ),
                    forecast_temperature=pred.forecast_temperature,
                    actual_temperature=actual_t,
                    temperature_error=round(actual_t - pred.forecast_temperature, 4),
                    forecast_humidity=pred.forecast_humidity,
                    actual_humidity=actual_h,
                    humidity_error=round(actual_h - pred.forecast_humidity, 4),
                )
                matched_target_key = target_iso
                break

        if matched_target_key:
            del self.pending_predictions[matched_target_key]

        # 3. Construct feature window strictly from past observations (<= current_index)
        # Slicing ensures NO future sensor records (> current_index) are accessible.
        window_start = max(0, self.current_index - 25)
        window_df = self.dataset_df.iloc[window_start : self.current_index + 1].copy()
        engineered_window = build_features(window_df)
        feature_row = engineered_window.iloc[-1][FEATURE_COLUMNS].to_dict()

        # 4. Generate 10-minute ML forecast
        pred_dict = self.predictor.predict(feature_row)
        predictions = PredictionPayload(
            forecast_temperature=pred_dict["future_temperature"],
            forecast_humidity=pred_dict["future_humidity"],
            predicted_occupancy=pred_dict["future_occupancy"],
            occupancy_probability=pred_dict["occupancy_probability"],
            prediction_horizon_minutes=pred_dict["prediction_horizon_minutes"],
        )

        # 5. Store pending prediction for future retrospective verification (t + 10m)
        target_timestamp = curr_timestamp + timedelta(minutes=10)
        self.pending_predictions[target_timestamp.isoformat()] = {
            "prediction": predictions,
            "timestamp": curr_timestamp,
        }

        # 6. Execute control policy step
        outcome = self.policy.step(sensors, predictions, self.appliance_state)
        self.appliance_state = outcome.new_state
        if outcome.events:
            self.event_log.extend(outcome.events)

        # 7. Extract future ground truth for retrospective display only (after prediction is made)
        future_ground_truth: Optional[Dict[str, Any]] = None
        # Look ahead 10 minutes in historical dataset strictly for evaluation metadata
        future_idx = self.current_index + 10
        if future_idx < self.total_records:
            future_row = self.dataset_df.iloc[future_idx]
            if abs((future_row["date"] - target_timestamp).total_seconds()) <= 15:
                future_ground_truth = {
                    "target_timestamp": future_row["date"],
                    "target_occupancy": int(future_row["Occupancy"]),
                    "target_temperature": float(future_row["Temperature"]),
                    "target_humidity": float(future_row["Humidity"]),
                    "target_light": float(future_row["Light"]),
                    "target_co2": float(future_row["CO2"]),
                }

        step_result = SimulationStepResult(
            step_index=self.current_index,
            timestamp=curr_timestamp,
            system_label=self.SYSTEM_LABEL,
            sensor_snapshot=sensors,
            prediction=predictions,
            appliance_state=self.appliance_state,
            transition_events=outcome.events,
            retrospective_evaluation=retro_eval,
            future_ground_truth=future_ground_truth,
        )

        self.history_steps.append(step_result)

        # Advance pointer
        self.current_index += 1
        if self.current_index >= self.total_records:
            self.status = SimulationStatus.COMPLETED

        return step_result
