# RoomIQ — Phase 2B Model Training & Evaluation Report

**Generated**: 2026-10-13T18:31:46.822176  
**Prediction Horizon**: 10 minutes ahead ($t + 10\text{ min}$)  
**Target Objectives**: Future Occupancy (0/1), Future Temperature (°C), Future Humidity (%)  

---

## 1. Chronological Splitting Design & Date Ranges

Evaluation strictly adheres to non-overlapping chronological boundaries to prevent temporal lookahead leakage:

| Split Partition | Source Split | Sample Count | Start Timestamp | End Timestamp | Purpose |
|---|---|---|---|---|---|
| **Training** | `datatraining.txt` (First 80%) | 6,498 | `2015-02-04 18:01:00` | `2015-02-09 06:17:59` | Model fitting |
| **Validation** | `datatraining.txt` (Last 20%) | 1,625 | `2015-02-09 06:19:00` | `2015-02-10 09:23:00` | Model tuning & selection |
| **Test Set 1** | `datatest.txt` | 2,645 | `2015-02-02 14:29:00` | `2015-02-04 10:33:00` | Historical out-of-sample holdout |
| **Test Set 2** | `datatest2.txt` | 9,732 | `2015-02-11 14:57:59` | `2015-02-18 09:08:59` | Future extended out-of-sample holdout |

> [!IMPORTANT]
> `Test Set 1` and `Test Set 2` were kept strictly out of model training, feature scaling, and tuning. All learned models were fit solely on the Chronological Training partition.

---

## 2. Objective 1: Future Occupancy Classification (10-min Horizon)

### 2.1 Model vs Baseline Comparison

| Evaluation Split | Model | Accuracy | Precision | Recall | F1-Score | ROC-AUC | Occupied Count (1) | Unoccupied Count (0) |
|---|---|---|---|---|---|---|---|---|
| **Validation** | **Random Forest** | 0.9729 | 0.9806 | 0.9439 | **0.9619** | 0.9928 | 588 | 1,037 |
| Validation | Majority-Class Baseline | 0.6382 | 0.0000 | 0.0000 | 0.0000 | N/A | 588 | 1,037 |
| **Test Set 1** | **Random Forest** | 0.8216 | 0.9181 | 0.5536 | **0.6907** | 0.9758 | 952 | 1,693 |
| Test Set 1 | Majority-Class Baseline | 0.6401 | 0.0000 | 0.0000 | 0.0000 | N/A | 952 | 1,693 |
| **Test Set 2** | **Random Forest** | 0.9483 | 0.9781 | 0.7693 | **0.8612** | 0.9622 | 2,029 | 7,703 |
| Test Set 2 | Majority-Class Baseline | 0.7915 | 0.0000 | 0.0000 | 0.0000 | N/A | 2,029 | 7,703 |

### 2.2 Confusion Matrices (Random Forest)

- **Validation Set**: TN = 1,026, FP = 11, FN = 33, TP = 555
- **Test Set 1**: TN = 1,646, FP = 47, FN = 425, TP = 527
- **Test Set 2**: TN = 7,668, FP = 35, FN = 468, TP = 1,561

---

## 3. Objective 2: Future Temperature Forecasting (10-min Horizon)

| Evaluation Split | Model | MAE (°C) | RMSE (°C) | R² Score | Actual Mean (°C) | Actual Std (°C) |
|---|---|---|---|---|---|---|
| **Validation** | **Random Forest Regressor** | **0.0862** | **0.1066** | 0.9797 | 20.69 | 0.75 |
| Validation | Persistence Baseline (T_t) | 0.0510 | 0.0777 | 0.9892 | 20.69 | 0.75 |
| **Test Set 1** | **Random Forest Regressor** | **0.1173** | **0.2130** | 0.9557 | 21.42 | 1.01 |
| Test Set 1 | Persistence Baseline (T_t) | 0.0569 | 0.0951 | 0.9912 | 21.42 | 1.01 |
| **Test Set 2** | **Random Forest Regressor** | **0.1222** | **0.2411** | 0.9442 | 21.00 | 1.02 |
| Test Set 2 | Persistence Baseline (T_t) | 0.0552 | 0.0871 | 0.9927 | 21.00 | 1.02 |

---

## 4. Objective 3: Future Humidity Forecasting (10-min Horizon)

| Evaluation Split | Model | MAE (%) | RMSE (%) | R² Score | Actual Mean (%) | Actual Std (%) |
|---|---|---|---|---|---|---|
| **Validation** | **Random Forest Regressor** | **3.0987** | **3.8122** | -0.6852 | 33.34 | 2.94 |
| Validation | Persistence Baseline (H_t) | 0.1745 | 0.2690 | 0.9916 | 33.34 | 2.94 |
| **Test Set 1** | **Random Forest Regressor** | **0.2793** | **0.4153** | 0.9711 | 25.35 | 2.44 |
| Test Set 1 | Persistence Baseline (H_t) | 0.1562 | 0.2412 | 0.9903 | 25.35 | 2.44 |
| **Test Set 2** | **Random Forest Regressor** | **1.5714** | **2.4478** | 0.6172 | 29.89 | 3.96 |
| Test Set 2 | Persistence Baseline (H_t) | 0.1747 | 0.2562 | 0.9958 | 29.89 | 3.96 |

---

## 5. Generalization Limitations & Honest Reporting

1. **Public Dataset Domain Constraints**: The evaluation is conducted entirely on the UCI Occupancy Detection benchmark (an office room with specific sensor placement and HVAC characteristics). High accuracy on this test set does not guarantee direct generalization to rooms with different window placements, natural sunlight exposures, room volumes, or occupancy densities.
2. **Sensor Redundancy & Darkness**: Ambient light is the dominant feature when artificial lighting is on; however, during dark periods or night occupancy (e.g., quiet study with desk lamp or movie viewing), the model must rely on the more subtle dynamics of CO2 and temperature.
3. **Zero Fan Classifier**: In accordance with dataset reality, no fan ON/OFF classifier was trained because fan-state labels do not exist in the source data.
