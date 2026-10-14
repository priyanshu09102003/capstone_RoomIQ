"""Health, model inventory, and offline evaluation metrics routes."""

from fastapi import APIRouter, Depends

from src.api.manager import SimulationManager, get_manager
from src.api.schemas import HealthResponse, MetricsResponse, ModelsMetadataResponse

router = APIRouter(tags=["Health & Models"])


@router.get("/health", response_model=HealthResponse)
async def get_health(manager: SimulationManager = Depends(get_manager)) -> HealthResponse:
    """Check service health, distinguishing API availability from model and dataset readiness."""
    return await manager.get_health()


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(manager: SimulationManager = Depends(get_manager)) -> MetricsResponse:
    """Retrieve offline model evaluation metrics for validation, test1, and test2 splits."""
    return await manager.get_metrics()


@router.get("/models", response_model=ModelsMetadataResponse)
async def get_models(manager: SimulationManager = Depends(get_manager)) -> ModelsMetadataResponse:
    """Retrieve loaded model inventory, feature names, prediction horizon, and dataset splits."""
    return await manager.get_models_info()
