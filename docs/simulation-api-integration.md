# RoomIQ — Simulation API Integration Blueprint (FastAPI Specification)

**System Classification**: DATASET REPLAY / SIMULATION  
**Target Module**: `ml/src/api/` (to be implemented in Phase 4B)  
**Consumer**: Next.js 16.4 Frontend (`frontend/src/`)

---

## 1. Architectural Overview

The `RoomIQSimulator` engine (`ml/src/simulation/`) operates as a stateful, deterministic replay core. In Phase 4B, it will be encapsulated within a thread-safe singleton manager in FastAPI.

```
┌────────────────────────────────────────────────────────┐
│                   Next.js Frontend                     │
│  - Playback Controls (Play, Pause, Step, Reset, Speed) │
│  - Live Sensor Telemetry Cards                         │
│  - 10-Minute Forecast Gauges                           │
│  - Virtual Fan / Light Status Badges                   │
│  - Retrospective Accuracy Indicator                    │
└──────────────────────────▲─────────────────────────────┘
                           │ HTTP REST & WebSocket / SSE
┌──────────────────────────▼─────────────────────────────┐
│                 FastAPI Backend Service                │
│                                                        │
│   ┌────────────────────────────────────────────────┐   │
│   │           Async Background Replay Loop         │   │
│   │   - Throttled sleep: (60s / playback_speed)    │   │
│   │   - Broadcasts step packets to active WS/SSE   │   │
│   └───────────────────────┬────────────────────────┘   │
│                           │ Calls step()               │
│   ┌───────────────────────▼────────────────────────┐   │
│   │               RoomIQSimulator Core             │   │
│   │   - Dynamic Feature Slicing (<= current_idx)   │   │
│   │   - RoomIQPredictor (Occupancy, Temp, Humidity)│   │
│   │   - RoomIQControlPolicy (Hysteresis & Timers)  │   │
│   └────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────┘
```

---

## 2. REST API Endpoints Specification

### 2.1 State & Lifecycle Management

| Method | Endpoint | Description | Request Body | Response Payload |
|---|---|---|---|---|
| `GET` | `/api/simulation/status` | Current playback state & summary telemetry | None | `SimulationStateSummary` |
| `POST` | `/api/simulation/start` | Starts automated chronological replay | None | `{"status": "RUNNING", "message": "Replay started"}` |
| `POST` | `/api/simulation/pause` | Pauses automated replay without resetting pointer | None | `{"status": "PAUSED", "message": "Replay paused"}` |
| `POST` | `/api/simulation/resume` | Resumes paused replay | None | `{"status": "RUNNING", "message": "Replay resumed"}` |
| `POST` | `/api/simulation/step` | Executes exactly one deterministic step | None | `SimulationStepResult` |
| `POST` | `/api/simulation/reset` | Resets pointer and virtual devices to initial state | None | `{"status": "IDLE", "message": "Simulator reset to initial state"}` |
| `POST` | `/api/simulation/speed` | Sets playback speed multiplier | `{"speed": 5.0}` | `{"playback_speed": 5.0}` |

### 2.2 Dynamic Policy Configuration

| Method | Endpoint | Description | Request Body | Response Payload |
|---|---|---|---|---|
| `GET` | `/api/control/config` | Retrieves current thresholds & timers | None | `ControlConfig` |
| `PUT` | `/api/control/config` | Updates policy thresholds dynamically | `ControlConfig` | `ControlConfig` |

---

## 3. Real-Time Streaming Specification (WebSocket & SSE)

### 3.1 WebSocket (`WS /api/simulation/ws`)
- **Direction**: Server-to-Client streaming with client control commands.
- **Message Format**:
```json
{
  "event": "step",
  "system_label": "DATASET REPLAY / SIMULATION",
  "step_index": 124,
  "timestamp": "2015-02-11T16:51:00",
  "sensor_snapshot": {
    "temperature": 21.76,
    "humidity": 31.13,
    "light": 437.33,
    "co2": 1029.67,
    "humidity_ratio": 0.005021
  },
  "prediction": {
    "prediction_horizon_minutes": 10,
    "predicted_occupancy": 1,
    "occupancy_probability": 0.942,
    "forecast_temperature": 22.04,
    "forecast_humidity": 31.25
  },
  "appliance_state": {
    "fan_on": true,
    "light_on": true
  },
  "transition_events": [
    {
      "device": "fan",
      "previous_state": false,
      "new_state": true,
      "decision_reason": "Forecast temp (22.80°C) >= ON threshold (22.50°C); switching ON"
    }
  ],
  "retrospective_evaluation": {
    "predicted_occupancy": 1,
    "actual_occupancy": 1,
    "occupancy_correct": true,
    "forecast_temperature": 21.90,
    "actual_temperature": 21.76,
    "temperature_error": -0.14
  }
}
```

---

## 4. Background Task Implementation Pattern in FastAPI

```python
import asyncio
from fastapi import FastAPI, BackgroundTasks, WebSocket
from src.simulation.simulator import RoomIQSimulator

app = FastAPI(title="RoomIQ API", version="1.0.0")
simulator = RoomIQSimulator()

async def background_replay_worker():
    while True:
        if simulator.status == SimulationStatus.RUNNING:
            try:
                step_result = simulator.step()
                await broadcast_to_websockets(step_result)
            except StopIteration:
                simulator.status = SimulationStatus.COMPLETED
                await broadcast_completion()
            
            # Throttle delay according to configured speed
            delay = 1.0 / simulator.config.playback_speed
            await asyncio.sleep(delay)
        else:
            await asyncio.sleep(0.1)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_replay_worker())
```

---

## 5. Security & Isolation Guarantees

1. **No External Actuation**: Virtual appliance states never trigger external network commands, GPIO switches, or MQTT topics.
2. **Deterministic Single-Step**: Calling `/api/simulation/step` always executes exactly one deterministic cycle.
3. **Reproducibility Guarantee**: Calling `/api/simulation/reset` guarantees that re-running from index $k$ produces identical output traces.
