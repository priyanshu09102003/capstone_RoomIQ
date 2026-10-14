"""Model training, evaluation, and serialization pipeline for RoomIQ."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    mean_absolute_error,
    root_mean_squared_error,
    r2_score,
)

from src.features.features import prepare_modeling_split, FEATURE_COLUMNS
from src.models.models import (
    create_occupancy_classifier,
    create_occupancy_baseline,
    create_temperature_regressor,
    create_temperature_baseline,
    create_humidity_regressor,
    create_humidity_baseline,
)


def evaluate_classification(
    y_true: pd.Series,
    y_pred: np.ndarray,
    y_prob: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    """Calculate comprehensive classification metrics handling undefined states explicitly."""
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
        },
        "sample_count": len(y_true),
        "unoccupied_count": int((y_true == 0).sum()),
        "occupied_count": int((y_true == 1).sum()),
        "occupied_percentage": float((y_true == 1).mean() * 100),
    }

    if y_prob is not None and len(np.unique(y_true)) > 1:
        try:
            metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob))
        except Exception:
            metrics["roc_auc"] = None
    else:
        metrics["roc_auc"] = None

    return metrics


def evaluate_regression(
    y_true: pd.Series,
    y_pred: np.ndarray,
) -> Dict[str, Any]:
    """Calculate regression metrics: MAE, RMSE, R2."""
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(root_mean_squared_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
        "sample_count": len(y_true),
        "mean_actual": float(np.mean(y_true)),
        "std_actual": float(np.std(y_true)),
    }


def plot_confusion_matrices(
    results: Dict[str, Any],
    output_path: Path,
):
    """Plot confusion matrices for validation and test sets."""
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    splits = [
        ("Validation Set", results["val"]["occupancy"]["model"]["confusion_matrix"]),
        ("Test Set 1 (datatest)", results["test1"]["occupancy"]["model"]["confusion_matrix"]),
        ("Test Set 2 (datatest2)", results["test2"]["occupancy"]["model"]["confusion_matrix"]),
    ]

    for idx, (title, cm_dict) in enumerate(splits):
        ax = axes[idx]
        matrix = np.array([
            [cm_dict["tn"], cm_dict["fp"]],
            [cm_dict["fn"], cm_dict["tp"]],
        ])
        sns.heatmap(
            matrix,
            annot=True,
            fmt="d",
            cmap="Blues",
            cbar=False,
            xticklabels=["Empty (0)", "Occupied (1)"],
            yticklabels=["Empty (0)", "Occupied (1)"],
            ax=ax,
        )
        ax.set_title(title, weight="bold")
        ax.set_xlabel("Predicted Label (t+10m)")
        ax.set_ylabel("True Label (t+10m)")

    plt.suptitle("RoomIQ — Future Occupancy (10-min Horizon) Confusion Matrices", weight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved confusion matrices plot -> {output_path}")


def plot_residuals(
    actuals: Dict[str, pd.Series],
    predictions: Dict[str, np.ndarray],
    target_name: str,
    units: str,
    output_path: Path,
):
    """Plot predicted vs actual and residual distribution."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    y_true = actuals[target_name].to_numpy()
    y_pred = predictions[target_name]
    residuals = y_true - y_pred

    # Scatter plot
    ax0 = axes[0]
    ax0.scatter(y_true, y_pred, alpha=0.3, s=10, color="#2980b9")
    min_val = min(y_true.min(), y_pred.min())
    max_val = max(y_true.max(), y_pred.max())
    ax0.plot([min_val, max_val], [min_val, max_val], "r--", linewidth=1.5, label="Ideal 1:1")
    ax0.set_xlabel(f"Actual {target_name.capitalize()} ({units})")
    ax0.set_ylabel(f"Predicted {target_name.capitalize()} ({units})")
    ax0.set_title(f"{target_name.capitalize()} Forecast: Actual vs Predicted", weight="bold")
    ax0.legend()

    # Residuals histogram
    ax1 = axes[1]
    sns.histplot(residuals, kde=True, ax=ax1, color="#27ae60", bins=40)
    ax1.set_xlabel(f"Residual ({target_name.capitalize()} Error, {units})")
    ax1.set_ylabel("Frequency")
    ax1.set_title(f"{target_name.capitalize()} Residual Distribution (Mean: {residuals.mean():.3f})", weight="bold")

    plt.suptitle(f"RoomIQ — 10-Minute {target_name.capitalize()} Forecast Residuals (Test Set 2)", weight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {target_name} residuals plot -> {output_path}")


def plot_feature_importances(
    models: Dict[str, Any],
    feature_names: List[str],
    output_path: Path,
):
    """Plot top 15 feature importances across all 3 trained models."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 7))

    for idx, (target_name, model) in enumerate(models.items()):
        ax = axes[idx]
        importances = model.feature_importances_
        top_indices = np.argsort(importances)[-12:]
        top_features = [feature_names[i] for i in top_indices]
        top_scores = importances[top_indices]

        ax.barh(range(len(top_indices)), top_scores, color="#3498db")
        ax.set_yticks(range(len(top_indices)))
        ax.set_yticklabels(top_features)
        ax.set_title(f"{target_name.capitalize()} Model Top Features", weight="bold")
        ax.set_xlabel("Relative Importance")

    plt.suptitle("RoomIQ — Top Predictive Feature Importances (Random Forest)", weight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved feature importances plot -> {output_path}")


def generate_evaluation_markdown(
    results: Dict[str, Any],
    metadata: Dict[str, Any],
    output_path: Path,
):
    """Generate comprehensive evaluation report markdown document."""
    lines = [
        "# RoomIQ — Phase 2B Model Training & Evaluation Report",
        "",
        f"**Generated**: {metadata['training_timestamp']}  ",
        f"**Prediction Horizon**: {metadata['prediction_horizon_minutes']} minutes ahead ($t + 10\\text{{ min}}$)  ",
        "**Target Objectives**: Future Occupancy (0/1), Future Temperature (°C), Future Humidity (%)  ",
        "",
        "---",
        "",
        "## 1. Chronological Splitting Design & Date Ranges",
        "",
        "Evaluation strictly adheres to non-overlapping chronological boundaries to prevent temporal lookahead leakage:",
        "",
        "| Split Partition | Source Split | Sample Count | Start Timestamp | End Timestamp | Purpose |",
        "|---|---|---|---|---|---|",
        f"| **Training** | `datatraining.txt` (First 80%) | {metadata['sample_counts']['train']:,} | `{metadata['date_ranges']['train']['start']}` | `{metadata['date_ranges']['train']['end']}` | Model fitting |",
        f"| **Validation** | `datatraining.txt` (Last 20%) | {metadata['sample_counts']['val']:,} | `{metadata['date_ranges']['val']['start']}` | `{metadata['date_ranges']['val']['end']}` | Model tuning & selection |",
        f"| **Test Set 1** | `datatest.txt` | {metadata['sample_counts']['test1']:,} | `{metadata['date_ranges']['test1']['start']}` | `{metadata['date_ranges']['test1']['end']}` | Historical out-of-sample holdout |",
        f"| **Test Set 2** | `datatest2.txt` | {metadata['sample_counts']['test2']:,} | `{metadata['date_ranges']['test2']['start']}` | `{metadata['date_ranges']['test2']['end']}` | Future extended out-of-sample holdout |",
        "",
        "> [!IMPORTANT]",
        "> `Test Set 1` and `Test Set 2` were kept strictly out of model training, feature scaling, and tuning. All learned models were fit solely on the Chronological Training partition.",
        "",
        "---",
        "",
        "## 2. Objective 1: Future Occupancy Classification (10-min Horizon)",
        "",
        "### 2.1 Model vs Baseline Comparison",
        "",
        "| Evaluation Split | Model | Accuracy | Precision | Recall | F1-Score | ROC-AUC | Occupied Count (1) | Unoccupied Count (0) |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    for split_key, split_label in [("val", "Validation"), ("test1", "Test Set 1"), ("test2", "Test Set 2")]:
        occ_model = results[split_key]["occupancy"]["model"]
        occ_base = results[split_key]["occupancy"]["baseline"]
        lines.append(
            f"| **{split_label}** | **Random Forest** | {occ_model['accuracy']:.4f} | {occ_model['precision']:.4f} | "
            f"{occ_model['recall']:.4f} | **{occ_model['f1']:.4f}** | {occ_model['roc_auc']:.4f} | "
            f"{occ_model['occupied_count']:,} | {occ_model['unoccupied_count']:,} |"
        )
        lines.append(
            f"| {split_label} | Majority-Class Baseline | {occ_base['accuracy']:.4f} | {occ_base['precision']:.4f} | "
            f"{occ_base['recall']:.4f} | {occ_base['f1']:.4f} | N/A | "
            f"{occ_base['occupied_count']:,} | {occ_base['unoccupied_count']:,} |"
        )

    lines.extend([
        "",
        "### 2.2 Confusion Matrices (Random Forest)",
        "",
        "- **Validation Set**: "
        f"TN = {results['val']['occupancy']['model']['confusion_matrix']['tn']:,}, "
        f"FP = {results['val']['occupancy']['model']['confusion_matrix']['fp']:,}, "
        f"FN = {results['val']['occupancy']['model']['confusion_matrix']['fn']:,}, "
        f"TP = {results['val']['occupancy']['model']['confusion_matrix']['tp']:,}",
        "- **Test Set 1**: "
        f"TN = {results['test1']['occupancy']['model']['confusion_matrix']['tn']:,}, "
        f"FP = {results['test1']['occupancy']['model']['confusion_matrix']['fp']:,}, "
        f"FN = {results['test1']['occupancy']['model']['confusion_matrix']['fn']:,}, "
        f"TP = {results['test1']['occupancy']['model']['confusion_matrix']['tp']:,}",
        "- **Test Set 2**: "
        f"TN = {results['test2']['occupancy']['model']['confusion_matrix']['tn']:,}, "
        f"FP = {results['test2']['occupancy']['model']['confusion_matrix']['fp']:,}, "
        f"FN = {results['test2']['occupancy']['model']['confusion_matrix']['fn']:,}, "
        f"TP = {results['test2']['occupancy']['model']['confusion_matrix']['tp']:,}",
        "",
        "---",
        "",
        "## 3. Objective 2: Future Temperature Forecasting (10-min Horizon)",
        "",
        "| Evaluation Split | Model | MAE (°C) | RMSE (°C) | R² Score | Actual Mean (°C) | Actual Std (°C) |",
        "|---|---|---|---|---|---|---|",
    ])

    for split_key, split_label in [("val", "Validation"), ("test1", "Test Set 1"), ("test2", "Test Set 2")]:
        t_model = results[split_key]["temperature"]["model"]
        t_base = results[split_key]["temperature"]["baseline"]
        lines.append(
            f"| **{split_label}** | **Random Forest Regressor** | **{t_model['mae']:.4f}** | **{t_model['rmse']:.4f}** | "
            f"{t_model['r2']:.4f} | {t_model['mean_actual']:.2f} | {t_model['std_actual']:.2f} |"
        )
        lines.append(
            f"| {split_label} | Persistence Baseline (T_t) | {t_base['mae']:.4f} | {t_base['rmse']:.4f} | "
            f"{t_base['r2']:.4f} | {t_base['mean_actual']:.2f} | {t_base['std_actual']:.2f} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 4. Objective 3: Future Humidity Forecasting (10-min Horizon)",
        "",
        "| Evaluation Split | Model | MAE (%) | RMSE (%) | R² Score | Actual Mean (%) | Actual Std (%) |",
        "|---|---|---|---|---|---|---|",
    ])

    for split_key, split_label in [("val", "Validation"), ("test1", "Test Set 1"), ("test2", "Test Set 2")]:
        h_model = results[split_key]["humidity"]["model"]
        h_base = results[split_key]["humidity"]["baseline"]
        lines.append(
            f"| **{split_label}** | **Random Forest Regressor** | **{h_model['mae']:.4f}** | **{h_model['rmse']:.4f}** | "
            f"{h_model['r2']:.4f} | {h_model['mean_actual']:.2f} | {h_model['std_actual']:.2f} |"
        )
        lines.append(
            f"| {split_label} | Persistence Baseline (H_t) | {h_base['mae']:.4f} | {h_base['rmse']:.4f} | "
            f"{h_base['r2']:.4f} | {h_base['mean_actual']:.2f} | {h_base['std_actual']:.2f} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 5. Generalization Limitations & Honest Reporting",
        "",
        "1. **Public Dataset Domain Constraints**: The evaluation is conducted entirely on the UCI Occupancy Detection benchmark (an office room with specific sensor placement and HVAC characteristics). High accuracy on this test set does not guarantee direct generalization to rooms with different window placements, natural sunlight exposures, room volumes, or occupancy densities.",
        "2. **Sensor Redundancy & Darkness**: Ambient light is the dominant feature when artificial lighting is on; however, during dark periods or night occupancy (e.g., quiet study with desk lamp or movie viewing), the model must rely on the more subtle dynamics of CO2 and temperature.",
        "3. **Zero Fan Classifier**: In accordance with dataset reality, no fan ON/OFF classifier was trained because fan-state labels do not exist in the source data.",
        "",
    ])

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def run_training_pipeline(
    data_dir: Path,
    artifacts_dir: Path,
    reports_dir: Path,
) -> Dict[str, Any]:
    """Execute complete training, evaluation, and artifact generation."""
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = reports_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    print("[1/5] Loading processed dataset splits...")
    df_train_raw = pd.read_csv(data_dir / "training_clean.csv")
    df_train_raw["date"] = pd.to_datetime(df_train_raw["date"])

    df_test1_raw = pd.read_csv(data_dir / "test_clean.csv")
    df_test1_raw["date"] = pd.to_datetime(df_test1_raw["date"])

    df_test2_raw = pd.read_csv(data_dir / "test2_clean.csv")
    df_test2_raw["date"] = pd.to_datetime(df_test2_raw["date"])

    print("[2/5] Preparing non-leaking features and aligned 10-minute targets...")
    X_train_full, y_train_full, stats_train = prepare_modeling_split(df_train_raw)
    X_test1, y_test1, stats_test1 = prepare_modeling_split(df_test1_raw)
    X_test2, y_test2, stats_test2 = prepare_modeling_split(df_test2_raw)

    # Chronological 80/20 train/validation split on training_clean.csv
    n_train_full = len(X_train_full)
    split_idx = int(n_train_full * 0.8)

    X_train = X_train_full.iloc[:split_idx].copy().reset_index(drop=True)
    y_train = {k: v.iloc[:split_idx].copy().reset_index(drop=True) for k, v in y_train_full.items()}

    X_val = X_train_full.iloc[split_idx:].copy().reset_index(drop=True)
    y_val = {k: v.iloc[split_idx:].copy().reset_index(drop=True) for k, v in y_train_full.items()}

    metadata = {
        "training_timestamp": datetime.now().isoformat(),
        "prediction_horizon_minutes": 10,
        "feature_names": FEATURE_COLUMNS,
        "sample_counts": {
            "train": len(X_train),
            "val": len(X_val),
            "test1": len(X_test1),
            "test2": len(X_test2),
            "total_usable": len(X_train) + len(X_val) + len(X_test1) + len(X_test2),
        },
        "date_ranges": {
            "train": {"start": str(y_train["date"].min()), "end": str(y_train["date"].max())},
            "val": {"start": str(y_val["date"].min()), "end": str(y_val["date"].max())},
            "test1": {"start": str(y_test1["date"].min()), "end": str(y_test1["date"].max())},
            "test2": {"start": str(y_test2["date"].min()), "end": str(y_test2["date"].max())},
        },
        "row_exclusions": {
            "training_split": stats_train,
            "test1_split": stats_test1,
            "test2_split": stats_test2,
        },
    }

    print(f"  - Chronological Train: {len(X_train):,} samples ({metadata['date_ranges']['train']['start']} to {metadata['date_ranges']['train']['end']})")
    print(f"  - Chronological Val:   {len(X_val):,} samples ({metadata['date_ranges']['val']['start']} to {metadata['date_ranges']['val']['end']})")
    print(f"  - Test 1 (datatest):   {len(X_test1):,} samples")
    print(f"  - Test 2 (datatest2):  {len(X_test2):,} samples")

    print("[3/5] Training candidate models and baselines...")
    # Model 1: Occupancy Classifier
    print("  - Fitting Occupancy RandomForestClassifier...")
    occ_model = create_occupancy_classifier()
    occ_model.fit(X_train, y_train["occupancy"])

    occ_baseline = create_occupancy_baseline()
    occ_baseline.fit(X_train, y_train["occupancy"])

    # Model 2: Temperature Regressor
    print("  - Fitting Temperature RandomForestRegressor...")
    temp_model = create_temperature_regressor()
    temp_model.fit(X_train, y_train["temperature"])

    temp_baseline = create_temperature_baseline()
    temp_baseline.fit(X_train, y_train["temperature"])

    # Model 3: Humidity Regressor
    print("  - Fitting Humidity RandomForestRegressor...")
    hum_model = create_humidity_regressor()
    hum_model.fit(X_train, y_train["humidity"])

    hum_baseline = create_humidity_baseline()
    hum_baseline.fit(X_train, y_train["humidity"])

    print("[4/5] Evaluating all models on Val, Test 1, and Test 2 sets...")
    eval_splits = {
        "val": (X_val, y_val),
        "test1": (X_test1, y_test1),
        "test2": (X_test2, y_test2),
    }

    results = {}
    predictions_test2 = {}

    for split_key, (X_eval, y_eval) in eval_splits.items():
        # Occupancy
        occ_pred = occ_model.predict(X_eval)
        occ_prob = occ_model.predict_proba(X_eval)[:, 1]
        occ_base_pred = occ_baseline.predict(X_eval)

        # Temperature
        temp_pred = temp_model.predict(X_eval)
        temp_base_pred = temp_baseline.predict(X_eval)

        # Humidity
        hum_pred = hum_model.predict(X_eval)
        hum_base_pred = hum_baseline.predict(X_eval)

        if split_key == "test2":
            predictions_test2["temperature"] = temp_pred
            predictions_test2["humidity"] = hum_pred

        results[split_key] = {
            "occupancy": {
                "model": evaluate_classification(y_eval["occupancy"], occ_pred, occ_prob),
                "baseline": evaluate_classification(y_eval["occupancy"], occ_base_pred),
            },
            "temperature": {
                "model": evaluate_regression(y_eval["temperature"], temp_pred),
                "baseline": evaluate_regression(y_eval["temperature"], temp_base_pred),
            },
            "humidity": {
                "model": evaluate_regression(y_eval["humidity"], hum_pred),
                "baseline": evaluate_regression(y_eval["humidity"], hum_base_pred),
            },
        }

    metadata["metrics"] = results

    print("[5/5] Saving serialized artifacts and generating evaluation reports...")
    # 1. Save Joblib models
    joblib.dump(occ_model, artifacts_dir / "occupancy_model.joblib")
    joblib.dump(temp_model, artifacts_dir / "temperature_model.joblib")
    joblib.dump(hum_model, artifacts_dir / "humidity_model.joblib")

    # 2. Save metadata JSON
    with open(artifacts_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    # 3. Generate Markdown report
    generate_evaluation_markdown(results, metadata, reports_dir / "model_evaluation_report.md")

    # 4. Generate Figures
    plot_confusion_matrices(results, figures_dir / "confusion_matrices.png")
    plot_residuals(y_test2, predictions_test2, "temperature", "°C", figures_dir / "temperature_residuals.png")
    plot_residuals(y_test2, predictions_test2, "humidity", "%", figures_dir / "humidity_residuals.png")
    plot_feature_importances(
        {"occupancy": occ_model, "temperature": temp_model, "humidity": hum_model},
        FEATURE_COLUMNS,
        figures_dir / "feature_importances.png",
    )

    print("=" * 65)
    print(" TRAINING & EVALUATION COMPLETED SUCCESSFULLY")
    print(f" Artifacts saved in: {artifacts_dir}")
    print(f" Reports saved in:   {reports_dir}")
    print("=" * 65)

    return metadata
