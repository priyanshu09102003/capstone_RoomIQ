# RoomIQ — Machine Learning & Data Pipeline

This directory contains the machine learning pipeline for RoomIQ: data ingestion, preprocessing, validation, exploratory data analysis, and test suites.

---

## 1. Directory Structure

```text
ml/
├── data/
│   ├── raw/                        # Untouched raw UCI sensor files
│   │   ├── datatest.txt            # Split 1: 2015-02-02 14:19:00 to 2015-02-04 10:43:00 (2,665 rows)
│   │   ├── datatraining.txt        # Split 2: 2015-02-04 17:51:00 to 2015-02-10 09:33:00 (8,143 rows)
│   │   └── datatest2.txt           # Split 3: 2015-02-11 14:48:00 to 2015-02-18 09:19:00 (9,752 rows)
│   └── processed/                  # Modeling-ready cleaned CSV files
│       ├── test_clean.csv
│       ├── test2_clean.csv
│       └── training_clean.csv
├── reports/                        # Quality audit and summary statistics
│   ├── data_quality_report.md
│   ├── summary_statistics.json
│   └── figures/                    # Generated EDA visualizations
│       ├── correlation_matrix.png
│       ├── feature_distributions.png
│       ├── occupancy_balance.png
│       └── timeseries_all_sensors.png
├── src/
│   └── data/                       # Modular pipeline components
│       ├── loader.py               # Safe data loading & schema validation
│       ├── preprocess.py           # Independent split feature engineering
│       ├── quality.py              # Statistical quality audit & gap analysis
│       └── visualize.py            # Publication-quality EDA plotting
├── tests/
│   └── test_data_loader.py         # Pytest test suite (14 unit tests)
├── requirements.txt                # Pinned dependencies (UTF-8)
└── run_preprocessing.py            # CLI entrypoint for preprocessing
```

---

## 2. Dataset Attribution & License

- **Dataset**: Occupancy Detection Data Set
- **Source**: [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/357/occupancy+detection)
- **Creators**: Luis M. Candanedo and V. Vélez (2016), University of Mons
- **Citation**: Candanedo, L.M. & Vélez, V. (2016). *Accurate occupancy detection of an office room from light, temperature, humidity and CO2 measurements using statistical learning models*. Energy and Buildings, 112, 28–39. DOI: [10.1016/j.enbuild.2016.01.001](https://doi.org/10.1016/j.enbuild.2016.01.001)
- **License**: [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)

---

## 3. Running Preprocessing & Model Training

### Step 1: Preprocessing & Data Quality Audit
```powershell
cd ml
.\.venv\Scripts\python run_preprocessing.py
```

### Step 2: Model Training & Evaluation (10-minute horizon)
```powershell
cd ml
.\.venv\Scripts\python run_training.py
```
This trains:
- Future Occupancy Classifier (RandomForestClassifier vs Majority baseline)
- Future Temperature Regressor (RandomForestRegressor vs Persistence baseline)
- Future Humidity Regressor (RandomForestRegressor vs Persistence baseline)

Outputs saved to:
- `ml/artifacts/`: `occupancy_model.joblib`, `temperature_model.joblib`, `humidity_model.joblib`, `metadata.json`
- `ml/reports/`: `model_evaluation_report.md`
- `ml/reports/figures/`: `confusion_matrices.png`, `temperature_residuals.png`, `humidity_residuals.png`, `feature_importances.png`

---

## 4. Running the Full Test Suite

Run pytest across all 22 tests (data loading, schema validation, temporal leakage prevention, target alignment, model serialization, inference):

```powershell
cd ml
.\.venv\Scripts\pytest tests -v
```

## 5. Automation Decision Engine (`ml/src/control/`)

RoomIQ includes a standalone, deterministic virtual appliance control policy engine:
- **Virtual Fan Actuation**: Driven by 10-minute forecast temperature with configurable hysteresis (`fan_temp_on_threshold=22.5°C`, `fan_temp_off_threshold=21.5°C`) and minimum switching intervals (`300s`) to avoid short-cycling.
- **Virtual Light Actuation**: Driven by predicted occupancy and recorded ambient lux (`light_lux_threshold=250.0 Lux`), with a vacancy delay timer (`light_vacancy_delay_seconds=300s`) to prevent premature turn-offs.
- **Device Independence**: Fan and light decisions are strictly independent.
- **Audit Logging**: Structured `TransitionEvent` objects are logged exclusively when an appliance changes state.

*Note: Device thresholds are demonstration defaults and have not been scientifically optimized. Virtual devices represent software simulations, not physical hardware.*

---

## 6. Running the Full Test Suite

Run pytest across all 37 tests (data loading, schema validation, leakage prevention, target alignment, model serialization, predictor inference, and decision engine):

```powershell
cd ml
.\.venv\Scripts\pytest tests -v
```

---

## 7. Inference & Control Smoke Test

Test end-to-end model inference and decision policy:

```powershell
cd ml
.\.venv\Scripts\python -c "from src.models.predictor import RoomIQPredictor; from src.control import RoomIQControlPolicy; print('Predictor and Control Policy initialized.')"
```

---

## 5. Temporal Independence & Splitting Constraints

The dataset consists of 3 distinct, non-contiguous chronological segments:
- **`datatest.txt`**: Feb 2 14:19 &rarr; Feb 4 10:43 (~1.85 days)
- *Gap 1*: **7 hours, 8 minutes**
- **`datatraining.txt`**: Feb 4 17:51 &rarr; Feb 10 09:33 (~5.65 days)
- *Gap 2*: **29 hours, 15 minutes**
- **`datatest2.txt`**: Feb 11 14:48 &rarr; Feb 18 09:19 (~6.77 days)

**Important Rule**: Do not concatenate the splits prior to computing lag or moving window features across time gaps. Each split must be processed within its independent chronological boundary.
