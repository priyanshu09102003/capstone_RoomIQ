"""Comprehensive API test suite for RoomIQ FastAPI backend service."""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.manager import SimulationManager, get_manager
from src.api.config import settings
from src.features.features import build_features, FEATURE_COLUMNS
from src.simulation.models import SimulationStatus
import pandas as pd


@pytest.fixture(scope="module")
def client():
    """Module-scoped FastAPI TestClient running the application lifespan."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def sample_feature_dict():
    """Extract a legitimate 50-feature dictionary from the test dataset."""
    csv_path = settings.data_dir / "test2_clean.csv"
    df = pd.read_csv(csv_path).iloc[:30].copy()
    df["date"] = pd.to_datetime(df["date"])
    features_df = build_features(df)
    return features_df.iloc[-1][FEATURE_COLUMNS].to_dict()


# --- Health & Models Endpoints ---

def test_health_endpoint_healthy(client: TestClient):
    """GET /api/health returns 200 with healthy state and models loaded."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["api_status"] == "online"
    assert data["models_ready"] is True
    assert data["data_ready"] is True
    assert data["system_label"] == "DATASET REPLAY / SIMULATION"
    assert data["details"]["features_count"] == 50
    assert data["details"]["horizon_minutes"] == 10


def test_health_endpoint_degraded():
    """GET /api/health correctly reports degraded when models are absent."""
    empty_mgr = SimulationManager()
    with TestClient(app) as test_client:
        app.dependency_overrides[get_manager] = lambda: empty_mgr
        try:
            resp = test_client.get("/api/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "degraded"
            assert data["models_ready"] is False
            assert data["data_ready"] is False
        finally:
            app.dependency_overrides.clear()


def test_metrics_endpoint(client: TestClient):
    """GET /api/metrics returns 200 with model evaluation metrics across all splits."""
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["system_label"] == "DATASET REPLAY / SIMULATION"
    assert "validation_metrics" in data
    assert "test1_metrics" in data
    assert "test2_metrics" in data
    assert "occupancy" in data["test2_metrics"]
    assert "temperature" in data["test2_metrics"]
    assert "humidity" in data["test2_metrics"]


def test_models_endpoint(client: TestClient):
    """GET /api/models returns 200 with model architecture, features, and horizon."""
    response = client.get("/api/models")
    assert response.status_code == 200
    data = response.json()
    assert data["system_label"] == "DATASET REPLAY / SIMULATION"
    assert data["prediction_horizon_minutes"] == 10
    assert data["total_features"] == 50
    assert len(data["features"]) == 50
    assert "Temperature" in data["features"]
    assert "CO2_roll_mean_15m" in data["features"]


# --- Inference Endpoint ---

def test_predict_success_with_features_key(client: TestClient, sample_feature_dict):
    """POST /api/predict succeeds with explicit features mapping."""
    payload = {"features": sample_feature_dict}
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["system_label"] == "DATASET REPLAY / SIMULATION"
    assert data["prediction_horizon_minutes"] == 10
    assert data["future_occupancy"] in (0, 1)
    assert 0.0 <= data["occupancy_probability"] <= 1.0
    assert isinstance(data["future_temperature"], float)
    assert isinstance(data["future_humidity"], float)


def test_predict_success_with_flat_dict(client: TestClient, sample_feature_dict):
    """POST /api/predict succeeds with flat feature payload."""
    response = client.post("/api/predict", json=sample_feature_dict)
    assert response.status_code == 200
    data = response.json()
    assert data["system_label"] == "DATASET REPLAY / SIMULATION"
    assert data["future_occupancy"] in (0, 1)


def test_predict_missing_features(client: TestClient):
    """POST /api/predict returns 422 when required features are missing."""
    payload = {"features": {"Temperature": 21.5, "Humidity": 30.0}}
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "Missing required feature columns" in data["error"] or "Missing required feature columns" in data["detail"]


def test_predict_nan_inf_features(client: TestClient, sample_feature_dict):
    """POST /api/predict returns 422 when feature values are non-numeric or null."""
    invalid_dict = dict(sample_feature_dict)
    invalid_dict["Temperature"] = None
    response = client.post("/api/predict", json={"features": invalid_dict})
    assert response.status_code == 422


# --- Simulation Endpoints ---

def test_simulation_status(client: TestClient):
    """GET /api/simulation/status returns 200 and initial state."""
    # Ensure reset first
    client.post("/api/simulation/reset")
    response = client.get("/api/simulation/status")
    assert response.status_code == 200
    data = response.json()
    assert data["system_label"] == "DATASET REPLAY / SIMULATION"
    assert data["status"] == "IDLE"
    assert data["current_index"] == 10
    assert data["total_records"] == 9752
    assert data["completed"] is False
    assert data["appliance_state"]["fan_on"] is False
    assert data["appliance_state"]["light_on"] is False


def test_simulation_step_success(client: TestClient):
    """POST /api/simulation/step executes a single deterministic step."""
    client.post("/api/simulation/reset")
    response = client.post("/api/simulation/step")
    assert response.status_code == 200
    data = response.json()
    assert data["system_label"] == "DATASET REPLAY / SIMULATION"
    assert data["step_index"] == 10
    assert "sensor_snapshot" in data
    assert "prediction" in data
    assert "appliance_state" in data
    assert "transition_events" in data

    # Verify pointer advanced
    status_resp = client.get("/api/simulation/status")
    assert status_resp.json()["current_index"] == 11


def test_simulation_lifecycle_pause_resume_reset(client: TestClient):
    """POST /api/simulation/pause, resume, and reset transition states correctly."""
    # Reset
    reset_resp = client.post("/api/simulation/reset")
    assert reset_resp.status_code == 200
    assert reset_resp.json()["status"] == "IDLE"

    # Pause
    pause_resp = client.post("/api/simulation/pause")
    assert pause_resp.status_code == 200

    # Resume
    resume_resp = client.post("/api/simulation/resume")
    assert resume_resp.status_code == 200

    # Reset restores index to 10
    client.post("/api/simulation/step")
    client.post("/api/simulation/step")
    assert client.get("/api/simulation/status").json()["current_index"] == 12

    client.post("/api/simulation/reset")
    assert client.get("/api/simulation/status").json()["current_index"] == 10


def test_simulation_step_conflict_when_running(client: TestClient):
    """POST /api/simulation/step returns 409 Conflict when simulation is actively running."""
    client.post("/api/simulation/reset")
    start_resp = client.post("/api/simulation/start")
    assert start_resp.status_code == 200
    assert start_resp.json()["status"] == "RUNNING"

    # Attempting to manually step while running must conflict
    step_resp = client.post("/api/simulation/step")
    assert step_resp.status_code == 409
    assert "Cannot manually step while continuous simulation is running" in step_resp.json()["detail"]

    # Pause to cleanup
    client.post("/api/simulation/pause")
    client.post("/api/simulation/reset")


# --- Events Endpoint ---

def test_events_endpoint(client: TestClient):
    """GET /api/events returns audit trail with filtering and limit."""
    client.post("/api/simulation/reset")
    # Step a few times to generate data
    for _ in range(5):
        client.post("/api/simulation/step")

    response = client.get("/api/events?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["system_label"] == "DATASET REPLAY / SIMULATION"
    assert isinstance(data["events"], list)
    assert isinstance(data["total_count"], int)


# --- Configuration Endpoints ---

def test_config_get(client: TestClient):
    """GET /api/config returns effective control thresholds and simulation settings."""
    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert data["system_label"] == "DATASET REPLAY / SIMULATION"
    assert data["control_config"]["fan_temp_on_threshold"] == 22.5
    assert data["control_config"]["fan_temp_off_threshold"] == 21.5
    assert data["control_config"]["fan_min_switching_interval_seconds"] == 300
    assert data["playback_speed"] == 1.0


def test_config_put_valid_update(client: TestClient):
    """PUT /api/config successfully updates threshold settings."""
    payload = {
        "fan_temp_on_threshold": 23.5,
        "fan_temp_off_threshold": 22.0,
        "playback_speed": 2.5,
    }
    response = client.put("/api/config", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["control_config"]["fan_temp_on_threshold"] == 23.5
    assert data["control_config"]["fan_temp_off_threshold"] == 22.0
    assert data["playback_speed"] == 2.5

    # Reset back to default
    restore_payload = {
        "fan_temp_on_threshold": 22.5,
        "fan_temp_off_threshold": 21.5,
        "playback_speed": 1.0,
    }
    client.put("/api/config", json=restore_payload)


def test_config_put_invalid_hysteresis(client: TestClient):
    """PUT /api/config rejects setting off_threshold >= on_threshold with 422."""
    payload = {
        "fan_temp_on_threshold": 21.0,
        "fan_temp_off_threshold": 23.0,
    }
    response = client.put("/api/config", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "must be strictly less than" in data["detail"]
