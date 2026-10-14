"""Real-time inference route for RoomIQ machine learning models."""

from fastapi import APIRouter, Depends

from src.api.manager import SimulationManager, get_manager
from src.api.schemas import PredictRequest, PredictResponse

router = APIRouter(tags=["Inference"])


@router.post("/predict", response_model=PredictResponse)
async def predict_future(
    request: PredictRequest, manager: SimulationManager = Depends(get_manager)
) -> PredictResponse:
    """Generate 10-minute horizon forecasts for occupancy, temperature, and humidity.

    Expects feature dictionary matching the model feature set.
    Never returns hardcoded or synthetic fallback values if inference fails.
    """
    return await manager.predict(request.features)
