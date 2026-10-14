"""Configuration settings for the RoomIQ FastAPI backend service."""

import os
from pathlib import Path
from typing import List
from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Runtime application settings for RoomIQ API."""

    app_name: str = "RoomIQ API"
    app_version: str = "1.0.0"
    system_label: str = "DATASET REPLAY / SIMULATION"
    debug: bool = Field(default=False)

    # Server binding
    host: str = Field(default_factory=lambda: os.getenv("ROOMIQ_HOST", "127.0.0.1"))
    port: int = Field(default_factory=lambda: int(os.getenv("ROOMIQ_PORT", "8000")))

    # CORS origins for Next.js frontend
    cors_origins: List[str] = Field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv(
                "ROOMIQ_CORS_ORIGINS",
                "http://localhost:3000,http://127.0.0.1:3000",
            ).split(",")
            if origin.strip()
        ]
    )

    # Resolved data and artifact paths
    base_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent.parent.parent
    )
    artifact_dir: Path = Field(default=Path())
    data_dir: Path = Field(default=Path())

    def __init__(self, **data):
        super().__init__(**data)
        if not self.artifact_dir or self.artifact_dir == Path():
            custom_art = os.getenv("ROOMIQ_ARTIFACT_DIR")
            self.artifact_dir = Path(custom_art) if custom_art else (self.base_dir / "artifacts")
        if not self.data_dir or self.data_dir == Path():
            custom_data = os.getenv("ROOMIQ_DATA_DIR")
            self.data_dir = Path(custom_data) if custom_data else (self.base_dir / "data" / "processed")


settings = Settings()
