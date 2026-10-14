"""Simulation playback, virtual actuation, and configuration routes."""

from typing import Optional
from fastapi import APIRouter, Depends, Query

from src.api.manager import SimulationManager, get_manager
from src.api.schemas import (
    ConfigUpdateRequest,
    EventsResponse,
    FullConfigResponse,
    SimulationActionResponse,
)
from src.simulation.models import SimulationStateSummary, SimulationStepResult

router = APIRouter(tags=["Simulation & Control"])


@router.get("/simulation/status", response_model=SimulationStateSummary)
async def get_simulation_status(
    manager: SimulationManager = Depends(get_manager),
) -> SimulationStateSummary:
    """Retrieve current replay pointer, playback speed, and virtual appliance telemetry."""
    return await manager.get_simulation_status()


@router.post("/simulation/start", response_model=SimulationActionResponse)
async def start_simulation(
    manager: SimulationManager = Depends(get_manager),
) -> SimulationActionResponse:
    """Begin automated chronological dataset replay in the background."""
    return await manager.start_simulation()


@router.post("/simulation/pause", response_model=SimulationActionResponse)
async def pause_simulation(
    manager: SimulationManager = Depends(get_manager),
) -> SimulationActionResponse:
    """Pause automated replay without losing the current sequence pointer."""
    return await manager.pause_simulation()


@router.post("/simulation/resume", response_model=SimulationActionResponse)
async def resume_simulation(
    manager: SimulationManager = Depends(get_manager),
) -> SimulationActionResponse:
    """Resume continuous background replay from current paused pointer."""
    return await manager.resume_simulation()


@router.post("/simulation/reset", response_model=SimulationActionResponse)
async def reset_simulation(
    manager: SimulationManager = Depends(get_manager),
) -> SimulationActionResponse:
    """Reset replay pointer and virtual appliances to initial state for reproducible replays."""
    return await manager.reset_simulation()


@router.post("/simulation/step", response_model=SimulationStepResult)
async def step_simulation(
    manager: SimulationManager = Depends(get_manager),
) -> SimulationStepResult:
    """Execute exactly one deterministic replay step.

    Returns the complete step payload including sensor readings, ML forecast,
    appliance actuation, state transitions, and matured retrospective evaluation.
    """
    return await manager.step_simulation()


@router.get("/events", response_model=EventsResponse)
async def get_transition_events(
    limit: Optional[int] = Query(default=100, ge=1, le=1000, description="Max events to return."),
    device: Optional[str] = Query(default=None, description="Filter by device ('fan' or 'light')."),
    manager: SimulationManager = Depends(get_manager),
) -> EventsResponse:
    """Retrieve virtual appliance state transition audit history."""
    return await manager.get_events(limit=limit, device=device)


@router.get("/config", response_model=FullConfigResponse)
async def get_configuration(
    manager: SimulationManager = Depends(get_manager),
) -> FullConfigResponse:
    """Retrieve current control policy thresholds, timers, and simulation parameters."""
    return await manager.get_config()


@router.put("/config", response_model=FullConfigResponse)
async def update_configuration(
    update: ConfigUpdateRequest,
    manager: SimulationManager = Depends(get_manager),
) -> FullConfigResponse:
    """Update automation decision thresholds, hysteresis bands, timers, or playback speed."""
    return await manager.update_config(update)
