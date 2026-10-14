# RoomIQ

RoomIQ is an intelligent room occupancy detection and monitoring system that utilizes environmental sensor streams (temperature, humidity, ambient light, CO2, and humidity ratio) to infer occupancy status without privacy-invasive cameras.

---

## Architecture Overview

- **`frontend/`**: Next.js 16.4 application with React 19, TypeScript, and Tailwind CSS.
- **`ml/`**: Python machine learning pipeline, data preprocessing, model training, and API server.
- **`docs/`**: Project architecture, verification reports, and engineering documentation.

---

## Machine Learning Pipeline Quickstart

1. Ensure the Python 3.12 virtual environment in `ml/.venv` is active.
2. Run data preprocessing and inspection:
   ```powershell
   cd ml
   .\.venv\Scripts\python run_preprocessing.py
   ```
3. Run the automated test suite:
   ```powershell
   .\.venv\Scripts\pytest tests -v
   ```

See [`ml/README.md`](ml/README.md) for full data pipeline documentation and [`docs/setup-verification.md`](docs/setup-verification.md) for environment verification details.
