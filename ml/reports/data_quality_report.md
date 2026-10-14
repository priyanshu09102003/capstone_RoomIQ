# RoomIQ — Comprehensive Data Quality Audit Report

**Generated Automatically During Phase 2A Pipeline Execution**  
**Source**: UCI Occupancy Detection Data Set (Candanedo & Vélez, 2016)  

---

## 1. Executive Summary

- **Integrity Verdict**: High quality. Zero missing values, zero corrupted rows, and zero duplicate timestamps.
- **Total Observations**: 20,560 data rows across 3 independent splits.
- **Sampling Rate**: ~1 minute intervals with ±1s hardware clock jitter (59s, 60s, 61s).
- **Critical Architectural Rule**: **Discontinuous Time Horizons**. The 3 splits are non-contiguous in time and separated by multi-hour gaps. They must not be merged naively when computing temporal lag features.

---

## 2. File Metadata & Overview

| Split | File Name | Size (Bytes) | Row Count | Start Timestamp | End Timestamp | Time Span |
|---|---|---|---|---|---|---|
| `test` | `datatest.txt` | 200,766 | 2,665 | `2015-02-02 14:19:00` | `2015-02-04 10:43:00` | 1 days 20:24:00 |
| `training` | `datatraining.txt` | 596,674 | 8,143 | `2015-02-04 17:51:00` | `2015-02-10 09:33:00` | 5 days 15:42:00 |
| `test2` | `datatest2.txt` | 699,664 | 9,752 | `2015-02-11 14:48:00` | `2015-02-18 09:19:00` | 6 days 18:31:00 |

---

## 3. Missing Value & Duplicate Analysis

| Split | Missing Values (Any Column) | Exact Duplicate Rows | Duplicate Timestamps |
|---|---|---|---|
| `training` | 0 | 0 | 0 |
| `test` | 0 | 0 | 0 |
| `test2` | 0 | 0 | 0 |

> [!NOTE]
> No data removal, synthetic interpolation, or imputation was required because all fields in every row are complete.

---

## 4. Timestamp & Sampling Gap Analysis

### 4.1 Internal Continuity Within Each File
Within each individual file, sensor logging occurred continuously once per minute:

- **Training Split**: 4,884 steps @ 60s, 1,629 steps @ 59s, 1,629 steps @ 61s. Gaps > 61s: **0**.
- **Test Split**: 1,596 steps @ 60s, 534 steps @ 59s, 534 steps @ 61s. Gaps > 61s: **0**.
- **Test2 Split**: 5,849 steps @ 60s, 1,951 steps @ 59s, 1,951 steps @ 61s. Gaps > 61s: **0**.

### 4.2 Inter-Split Time Gaps (Chronological Sequence)

| Chronological Transition | Prior Split End | Next Split Start | Gap Duration |
|---|---|---|---|
| `test` &rarr; `training` | `2015-02-04 10:43:00` | `2015-02-04 17:51:00` | **7.13 hours** (0 days 07:08:00) |
| `training` &rarr; `test2` | `2015-02-10 09:33:00` | `2015-02-11 14:48:00` | **29.25 hours** (1 days 05:15:00) |

> [!WARNING]
> `datatest.txt` chronologically occurs **before** `datatraining.txt`. `datatest2.txt` occurs **after** `datatraining.txt`. Rolling window or lag features must be calculated strictly within each split boundary.

---

## 5. Class Distribution & Target Imbalance

| Split | Unoccupied (0) Count | Occupied (1) Count | Occupied % |
|---|---|---|---|
| `training` | 6,414 | 1,729 | 21.23% |
| `test` | 1,693 | 972 | 36.47% |
| `test2` | 7,703 | 2,049 | 21.01% |

---

## 6. Sensor Variable Summary Statistics

### Split: `training`
| Variable | Min | 25% | Median | Mean | 75% | Max | Std Dev |
|---|---|---|---|---|---|---|---|
| **Temperature** | 19.00 | 19.70 | 20.39 | 20.62 | 21.39 | 23.18 | 1.02 |
| **Humidity** | 16.75 | 20.20 | 26.22 | 25.73 | 30.53 | 39.12 | 5.53 |
| **Light** | 0.00 | 0.00 | 0.00 | 119.52 | 256.38 | 1546.33 | 194.76 |
| **CO2** | 412.75 | 439.00 | 453.50 | 606.55 | 638.83 | 2028.50 | 314.32 |
| **HumidityRatio** | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 |

### Split: `test`
| Variable | Min | 25% | Median | Mean | 75% | Max | Std Dev |
|---|---|---|---|---|---|---|---|
| **Temperature** | 20.20 | 20.65 | 20.89 | 21.43 | 22.36 | 24.41 | 1.03 |
| **Humidity** | 22.10 | 23.26 | 25.00 | 25.35 | 26.86 | 31.47 | 2.44 |
| **Light** | 0.00 | 0.00 | 0.00 | 193.23 | 442.50 | 1697.25 | 250.21 |
| **CO2** | 427.50 | 466.00 | 580.50 | 717.91 | 956.33 | 1402.25 | 292.68 |
| **HumidityRatio** | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 |

### Split: `test2`
| Variable | Min | 25% | Median | Mean | 75% | Max | Std Dev |
|---|---|---|---|---|---|---|---|
| **Temperature** | 19.50 | 20.29 | 20.79 | 21.00 | 21.53 | 24.39 | 1.02 |
| **Humidity** | 21.86 | 26.64 | 30.20 | 29.89 | 32.70 | 39.50 | 3.95 |
| **Light** | 0.00 | 0.00 | 0.00 | 123.07 | 208.25 | 1581.00 | 208.22 |
| **CO2** | 484.67 | 542.31 | 639.00 | 753.22 | 831.12 | 2076.50 | 297.10 |
| **HumidityRatio** | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 |

---

## 7. Data Limitations for Forecasting & Modeling

1. **Sampling Resolution**: 1-minute resolution captures fast light switches and human entry, but CO2 and temperature have significant thermal inertia.
2. **Sensor Dominance**: Light level is zero during all nights and unlit periods. When lights are off, detection depends entirely on subtle CO2 and temperature/humidity dynamics.
3. **Discontinuous Test Sets**: Models must be evaluated on chronological out-of-sample segments without cross-split leakage.
