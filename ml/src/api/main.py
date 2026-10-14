"""Main FastAPI application factory and entrypoint for RoomIQ."""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.config import settings
from src.api.manager import get_manager
from src.api.routes.health import router as health_router
from src.api.routes.prediction import router as prediction_router
from src.api.routes.simulation import router as simulation_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("roomiq.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle context manager."""
    logger.info("Starting RoomIQ backend service...")
    manager = get_manager()
    await manager.initialize()
    yield
    logger.info("Shutting down RoomIQ backend service...")
    await manager.shutdown()


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(
        title="RoomIQ API",
        description=(
            "Machine Learning Inference, Deterministic Dataset Replay, "
            "and Automation Decision Engine for RoomIQ.\n\n"
            "SYSTEM CLASSIFICATION: DATASET REPLAY / SIMULATION"
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    # Configure CORS for local Next.js frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register Routers
    app.include_router(health_router, prefix="/api")
    app.include_router(prediction_router, prefix="/api")
    app.include_router(simulation_router, prefix="/api")

    # Exception Handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Format request validation errors cleanly without exposing internals."""
        errors = []
        for err in exc.errors():
            loc = " -> ".join(str(l) for l in err.get("loc", []))
            errors.append({"location": loc, "message": err.get("msg")})
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "system_label": settings.system_label,
                "error": "Validation Error",
                "details": errors,
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Standardized JSON format for HTTP exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "system_label": settings.system_label,
                "error": exc.detail if isinstance(exc.detail, str) else "Request Error",
                "detail": exc.detail,
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Mask internal server errors and log traceback internally."""
        logger.error(f"Unhandled server error on {request.method} {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "system_label": settings.system_label,
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred while processing the request.",
            },
        )

    return app


app = create_app()
