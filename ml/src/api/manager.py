"""Thread-safe state manager for RoomIQ ML inference and simulation replay."""

import asyncio
from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status

from src.api.config import settings
from src.api.schemas import (
    ConfigUpdateRequest,
    EventsResponse,
    FullConfigResponse,
    HealthResponse,
    MetricsResponse,
    ModelsMetadataResponse,
    PredictResponse,
    SimulationActionResponse,
)
from src.control.models import ControlConfig
from src.models.predictor import RoomIQPredictor
from src.simulation.models import SimulationStateSummary, SimulationStatus, SimulationStepResult
from src.simulation.simulator import RoomIQSimulator

logger = logging.getLogger("roomiq.manager")


class SimulationManager:
    """Singleton service managing model readiness, thread-safe replay, and automation policies."""

    def __init__(self):
        self._lock = asyncio.Lock()
        self.predictor: Optional[RoomIQPredictor] = None
        self.simulator: Optional[RoomIQSimulator] = None
        self.metadata: Optional[Dict[str, Any]] = None
        self.load_error: Optional[str] = None
        self._worker_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    async def initialize(self):
        """Load artifacts, initialize simulation engine, and launch background worker."""
        try:
            logger.info("Initializing RoomIQ Predictor and Simulator...")
            meta_path = settings.artifact_dir / "metadata.json"
            if meta_path.exists():
                with open(meta_path, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)

            self.predictor = RoomIQPredictor.load(settings.artifact_dir)
            self.simulator = RoomIQSimulator(
                data_dir=settings.data_dir,
                artifact_dir=settings.artifact_dir,
            )
            self.load_error = None
            logger.info("RoomIQ Predictor and Simulator initialized successfully.")
        except Exception as exc:
            self.load_error = f"Model/Data initialization failed: {type(exc).__name__}"
            logger.warning(f"Failed to initialize models/simulator: {exc}")

        # Start asynchronous background worker loop
        self._stop_event.clear()
        self._worker_task = asyncio.create_task(self._replay_worker())

    async def shutdown(self):
        """Gracefully stop background loop on application termination."""
        self._stop_event.set()
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

    async def _replay_worker(self):
        """Continuous background replay runner executing periodic steps when RUNNING."""
        while not self._stop_event.is_set():
            try:
                if self.simulator and self.simulator.status == SimulationStatus.RUNNING:
                    speed = max(0.1, self.simulator.config.playback_speed)
                    step_delay = 1.0 / speed

                    async with self._lock:
                        if self.simulator.status == SimulationStatus.RUNNING:
                            try:
                                self.simulator.step()
                            except StopIteration:
                                logger.info("Background replay completed: reached dataset bounds.")
                                self.simulator.status = SimulationStatus.COMPLETED
                            except Exception as step_exc:
                                logger.error(f"Replay stepping error: {step_exc}")
                                self.simulator.status = SimulationStatus.PAUSED

                    await asyncio.sleep(step_delay)
                else:
                    await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break
            except Exception as loop_exc:
                logger.error(f"Unexpected error in background worker: {loop_exc}")
                await asyncio.sleep(0.5)

    def _require_predictor(self) -> RoomIQPredictor:
        if not self.predictor:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Model artifacts unavailable. {self.load_error or 'Please verify trained artifacts.'}",
            )
        return self.predictor

    def _require_simulator(self) -> RoomIQSimulator:
        if not self.simulator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Simulation dataset unavailable. {self.load_error or 'Please verify processed datasets.'}",
            )
        return self.simulator

    # --- Health & Models Endpoints ---

    async def get_health(self) -> HealthResponse:
        models_ready = self.predictor is not None
        data_ready = self.simulator is not None
        overall_healthy = models_ready and data_ready

        details = {
            "predictor_ready": models_ready,
            "simulator_ready": data_ready,
            "horizon_minutes": 10 if models_ready else None,
            "features_count": len(self.predictor.feature_names) if models_ready else 0,
        }
        if self.load_error:
            details["error"] = self.load_error

        return HealthResponse(
            status="healthy" if overall_healthy else "degraded",
            api_status="online",
            models_ready=models_ready,
            data_ready=data_ready,
            details=details,
        )

    async def get_metrics(self) -> MetricsResponse:
        self._require_predictor()
        if not self.metadata or "metrics" not in self.metadata:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Model evaluation metrics not found in artifact metadata.",
            )

        metrics = self.metadata.get("metrics", {})
        return MetricsResponse(
            training_timestamp=self.metadata.get("training_timestamp"),
            validation_metrics=metrics.get("val", {}),
            test1_metrics=metrics.get("test1", {}),
            test2_metrics=metrics.get("test2", {}),
        )

    async def get_models_info(self) -> ModelsMetadataResponse:
        predictor = self._require_predictor()
        meta = self.metadata or predictor.metadata or {}
        return ModelsMetadataResponse(
            prediction_horizon_minutes=predictor.prediction_horizon_minutes,
            features=predictor.feature_names,
            total_features=len(predictor.feature_names),
            training_timestamp=meta.get("training_timestamp"),
            sample_counts=meta.get("sample_counts"),
            date_ranges=meta.get("date_ranges"),
        )

    # --- Prediction Inference ---

    async def predict(self, features: Dict[str, float]) -> PredictResponse:
        predictor = self._require_predictor()

        missing = [f for f in predictor.feature_names if f not in features]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    f"Missing required feature columns: {missing[:5]} "
                    f"(total missing: {len(missing)} of {len(predictor.feature_names)})"
                ),
            )

        try:
            pred_dict = predictor.predict(features)
        except Exception as exc:
            logger.error(f"Model inference failed: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Model inference execution failed.",
            )

        return PredictResponse(
            prediction_horizon_minutes=pred_dict["prediction_horizon_minutes"],
            future_occupancy=pred_dict["future_occupancy"],
            occupancy_probability=pred_dict["occupancy_probability"],
            future_temperature=pred_dict["future_temperature"],
            future_humidity=pred_dict["future_humidity"],
        )

    # --- Simulation Operations ---

    async def get_simulation_status(self) -> SimulationStateSummary:
        simulator = self._require_simulator()
        async with self._lock:
            return simulator.get_summary()

    async def start_simulation(self) -> SimulationActionResponse:
        simulator = self._require_simulator()
        async with self._lock:
            if simulator.status == SimulationStatus.COMPLETED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot start completed simulation. Call /api/simulation/reset first.",
                )
            simulator.start()
            return SimulationActionResponse(
                status=simulator.status,
                message="Simulation replay started.",
                current_index=simulator.current_index,
            )

    async def pause_simulation(self) -> SimulationActionResponse:
        simulator = self._require_simulator()
        async with self._lock:
            simulator.pause()
            return SimulationActionResponse(
                status=simulator.status,
                message="Simulation replay paused.",
                current_index=simulator.current_index,
            )

    async def resume_simulation(self) -> SimulationActionResponse:
        simulator = self._require_simulator()
        async with self._lock:
            simulator.resume()
            return SimulationActionResponse(
                status=simulator.status,
                message="Simulation replay resumed.",
                current_index=simulator.current_index,
            )

    async def reset_simulation(self) -> SimulationActionResponse:
        simulator = self._require_simulator()
        async with self._lock:
            simulator.reset()
            return SimulationActionResponse(
                status=simulator.status,
                message="Simulation replay reset to initial state.",
                current_index=simulator.current_index,
            )

    async def step_simulation(self) -> SimulationStepResult:
        simulator = self._require_simulator()
        if simulator.status == SimulationStatus.RUNNING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot manually step while continuous simulation is running. Pause simulation first.",
            )

        async with self._lock:
            try:
                step_result = simulator.step()
                return step_result
            except StopIteration:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="End of simulation dataset reached. Call /api/simulation/reset to restart.",
                )

    async def get_events(
        self, limit: Optional[int] = None, device: Optional[str] = None
    ) -> EventsResponse:
        simulator = self._require_simulator()
        async with self._lock:
            events = list(simulator.event_log)

        if device:
            dev_lower = device.lower().strip()
            events = [e for e in events if e.device.lower() == dev_lower]

        if limit is not None and limit > 0:
            events = events[-limit:]

        return EventsResponse(
            events=events,
            total_count=len(simulator.event_log),
        )

    async def get_config(self) -> FullConfigResponse:
        simulator = self._require_simulator()
        async with self._lock:
            return FullConfigResponse(
                control_config=simulator.policy.config,
                playback_speed=simulator.config.playback_speed,
                split_name=simulator.config.split_name,
                start_index=simulator.config.start_index,
            )

    async def update_config(self, update: ConfigUpdateRequest) -> FullConfigResponse:
        simulator = self._require_simulator()
        async with self._lock:
            curr_ctrl = simulator.policy.config

            # Determine proposed thresholds
            new_on = (
                update.fan_temp_on_threshold
                if update.fan_temp_on_threshold is not None
                else curr_ctrl.fan_temp_on_threshold
            )
            new_off = (
                update.fan_temp_off_threshold
                if update.fan_temp_off_threshold is not None
                else curr_ctrl.fan_temp_off_threshold
            )

            if new_off >= new_on:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=(
                        f"fan_temp_off_threshold ({new_off}) must be strictly less than "
                        f"fan_temp_on_threshold ({new_on}) to maintain hysteresis."
                    ),
                )

            # Build updated ControlConfig
            new_ctrl = ControlConfig(
                fan_temp_on_threshold=new_on,
                fan_temp_off_threshold=new_off,
                fan_min_switching_interval_seconds=(
                    update.fan_min_switching_interval_seconds
                    if update.fan_min_switching_interval_seconds is not None
                    else curr_ctrl.fan_min_switching_interval_seconds
                ),
                light_lux_threshold=(
                    update.light_lux_threshold
                    if update.light_lux_threshold is not None
                    else curr_ctrl.light_lux_threshold
                ),
                light_vacancy_delay_seconds=(
                    update.light_vacancy_delay_seconds
                    if update.light_vacancy_delay_seconds is not None
                    else curr_ctrl.light_vacancy_delay_seconds
                ),
            )

            # Update simulator and policy in-place
            simulator.policy.config = new_ctrl
            simulator.config.control_config = new_ctrl

            if update.playback_speed is not None:
                simulator.set_speed(update.playback_speed)

            return FullConfigResponse(
                control_config=simulator.policy.config,
                playback_speed=simulator.config.playback_speed,
                split_name=simulator.config.split_name,
                start_index=simulator.config.start_index,
            )


# Global singleton manager instance
manager = SimulationManager()


def get_manager() -> SimulationManager:
    """Dependency provider for route handlers."""
    return manager
