"""RoomIQ FastAPI backend package."""

from src.api.main import app
from src.api.config import settings
from src.api.manager import SimulationManager, get_manager

__all__ = ["app", "settings", "SimulationManager", "get_manager"]
