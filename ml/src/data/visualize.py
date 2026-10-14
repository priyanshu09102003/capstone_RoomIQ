"""Exploratory Data Analysis (EDA) plotting module for RoomIQ."""

from pathlib import Path
from typing import Dict
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np


def setup_plotting_theme():
    """Apply clean aesthetics for publication-quality figures."""
    sns.set_theme(style="whitegrid", palette="muted")
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.labelsize": 12,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 11,
        "figure.titlesize": 15,
    })


def plot_timeseries_sensors(df: pd.DataFrame, output_path: Path):
    """Plot multi-panel time series of sensors with occupancy overlay.

    Args:
        df: Processed DataFrame containing 'date', sensors, and 'Occupancy'.
        output_path: Path to save the image.
    """
    setup_plotting_theme()
    sensors = [
        ("Temperature", "Temperature (°C)", "#e74c3c"),
        ("Humidity", "Humidity (%)", "#3498db"),
        ("Light", "Light (Lux)", "#f39c12"),
        ("CO2", "CO2 (ppm)", "#2ecc71"),
        ("HumidityRatio", "Humidity Ratio (kg/kg)", "#9b59b6"),
    ]

    fig, axes = plt.subplots(len(sensors) + 1, 1, figsize=(14, 12), sharex=True)
    fig.suptitle("RoomIQ — Training Sensor Readings & Occupancy Over Time", y=0.99, weight="bold")

    dates = pd.to_datetime(df["date"])

    for idx, (col, label, color) in enumerate(sensors):
        ax = axes[idx]
        ax.plot(dates, df[col], color=color, linewidth=1.2, label=col)
        ax.set_ylabel(label)
        ax.legend(loc="upper right")
        # Shade occupied periods
        ax.fill_between(
            dates,
            ax.get_ylim()[0],
            ax.get_ylim()[1],
            where=(df["Occupancy"] == 1),
            color="#e74c3c",
            alpha=0.15,
            label="Occupied Period" if idx == 0 else None,
        )

    # Bottom subplot: Occupancy step line
    ax_occ = axes[-1]
    ax_occ.step(dates, df["Occupancy"], color="#34495e", linewidth=1.5, where="post")
    ax_occ.set_ylabel("Occupancy")
    ax_occ.set_yticks([0, 1])
    ax_occ.set_yticklabels(["Empty (0)", "Occupied (1)"])
    ax_occ.set_xlabel("Timestamp")

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved timeseries plot -> {output_path}")


def plot_correlation_matrix(df: pd.DataFrame, output_path: Path):
    """Plot correlation heatmap among sensor variables and occupancy.

    Args:
        df: Processed DataFrame.
        output_path: Path to save heatmap.
    """
    setup_plotting_theme()
    feature_cols = [
        "Temperature",
        "Humidity",
        "Light",
        "CO2",
        "HumidityRatio",
        "hour",
        "day_of_week",
        "is_weekend",
        "Occupancy",
    ]

    corr = df[feature_cols].corr()

    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(
        corr,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        vmin=-1,
        vmax=1,
        square=True,
        cbar_kws={"shrink": 0.8, "label": "Pearson Correlation"},
        ax=ax,
    )
    ax.set_title("RoomIQ — Feature Correlation Heatmap", weight="bold", pad=15)

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved correlation matrix plot -> {output_path}")


def plot_feature_distributions(df: pd.DataFrame, output_path: Path):
    """Plot feature distributions conditioned on Occupancy state.

    Args:
        df: Processed DataFrame.
        output_path: Path to save boxplot grid.
    """
    setup_plotting_theme()
    sensors = [
        ("Temperature", "Temperature (°C)"),
        ("Humidity", "Humidity (%)"),
        ("Light", "Light (Lux)"),
        ("CO2", "CO2 (ppm)"),
        ("HumidityRatio", "Humidity Ratio (kg/kg)"),
    ]

    fig, axes = plt.subplots(1, 5, figsize=(18, 5))
    fig.suptitle("Sensor Value Distributions by Occupancy State", weight="bold", y=1.02)

    df_plot = df.copy()
    df_plot["Occupancy_Label"] = df_plot["Occupancy"].map({0: "Empty (0)", 1: "Occupied (1)"})

    palette = {"Empty (0)": "#3498db", "Occupied (1)": "#e74c3c"}

    for idx, (col, label) in enumerate(sensors):
        ax = axes[idx]
        sns.boxplot(
            data=df_plot,
            x="Occupancy_Label",
            y=col,
            hue="Occupancy_Label",
            legend=False,
            palette=palette,
            ax=ax,
            fliersize=2,
            boxprops=dict(alpha=0.8),
        )
        ax.set_title(col, weight="bold")
        ax.set_xlabel("")
        ax.set_ylabel(label)

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved feature distributions plot -> {output_path}")


def plot_class_balance(splits: Dict[str, pd.DataFrame], output_path: Path):
    """Plot class balance comparison across all splits.

    Args:
        splits: Dictionary of split DataFrames.
        output_path: Path to save bar chart.
    """
    setup_plotting_theme()
    records = []
    for split_name, df in splits.items():
        total = len(df)
        unoccupied = int((df["Occupancy"] == 0).sum())
        occupied = int((df["Occupancy"] == 1).sum())
        records.append({
            "Split": split_name.capitalize(),
            "State": "Empty (0)",
            "Count": unoccupied,
            "Percentage": (unoccupied / total) * 100,
        })
        records.append({
            "Split": split_name.capitalize(),
            "State": "Occupied (1)",
            "Count": occupied,
            "Percentage": (occupied / total) * 100,
        })

    balance_df = pd.DataFrame(records)

    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(
        data=balance_df,
        x="Split",
        y="Count",
        hue="State",
        palette={"Empty (0)": "#3498db", "Occupied (1)": "#e74c3c"},
        ax=ax,
    )
    ax.set_title("RoomIQ — Class Balance Across Dataset Splits", weight="bold", pad=15)
    ax.set_ylabel("Number of Observations")

    # Add count and percentage labels on bars
    for p in ax.patches:
        height = p.get_height()
        if height > 0:
            ax.annotate(
                f"{int(height):,}",
                (p.get_x() + p.get_width() / 2.0, height),
                ha="center",
                va="bottom",
                fontsize=9,
                xytext=(0, 3),
                textcoords="offset points",
            )

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved occupancy balance plot -> {output_path}")


def generate_all_plots(
    splits: Dict[str, pd.DataFrame],
    figures_dir: Path,
):
    """Generate and save all exploratory analysis figures.

    Args:
        splits: Loaded processed split DataFrames.
        figures_dir: Directory where figures will be saved.
    """
    figures_dir.mkdir(parents=True, exist_ok=True)
    training_df = splits["training"]

    plot_timeseries_sensors(training_df, figures_dir / "timeseries_all_sensors.png")
    plot_correlation_matrix(training_df, figures_dir / "correlation_matrix.png")
    plot_feature_distributions(training_df, figures_dir / "feature_distributions.png")
    plot_class_balance(splits, figures_dir / "occupancy_balance.png")
