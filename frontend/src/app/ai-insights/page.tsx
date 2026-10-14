"use client";

import React, { useEffect, useState } from "react";
import { BrainCircuit, Cpu, Database, LineChart, Target } from "lucide-react";
import { api } from "@/lib/api";
import { MetricsResponse, ModelsMetadataResponse } from "@/types/api";
import { ConnectionAlert } from "@/components/common/ConnectionAlert";
import { ConfusionMatrixCard } from "@/components/charts/ConfusionMatrixCard";
import { formatMetricScore, formatPercent, formatTimestamp } from "@/lib/formatters";

export default function AiInsightsPage() {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [modelsInfo, setModelsInfo] = useState<ModelsMetadataResponse | null>(null);
  const [activeSplit, setActiveSplit] = useState<"test2" | "val">("test2");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchML = async () => {
    setLoading(true);
    setError(null);
    try {
      const [m, info] = await Promise.all([api.getMetrics(), api.getModels()]);
      setMetrics(m);
      setModelsInfo(info);
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchML();
  }, []);

  const activeMetrics =
    activeSplit === "test2" ? metrics?.test2_metrics : metrics?.validation_metrics;

  const occupancyModel = (activeMetrics as Record<string, any>)?.occupancy?.model;
  const tempModel = (activeMetrics as Record<string, any>)?.temperature?.model;
  const humidityModel = (activeMetrics as Record<string, any>)?.humidity?.model;
  const cm = occupancyModel?.confusion_matrix;

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      <ConnectionAlert />

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <BrainCircuit className="w-5 h-5 text-purple-400" />
            <h1 className="text-xl font-bold text-slate-100">
              Model Performance & 10-Minute Forecast Insights
            </h1>
          </div>
          <p className="text-xs text-slate-400">
            Supervised learning models trained on 6,498 observations, validated on 1,625 samples, and benchmarked across Test 1 (2,645) and Test 2 (9,732) partitions.
            {modelsInfo?.training_timestamp && (
              <span className="block mt-0.5 text-[11px] text-slate-500 font-mono">
                Model training artifact generated: {formatTimestamp(modelsInfo.training_timestamp)}
              </span>
            )}
          </p>
        </div>

        {/* Split Toggle */}
        <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
          <button
            onClick={() => setActiveSplit("test2")}
            className={`px-3 py-1.5 rounded transition-colors font-mono ${
              activeSplit === "test2"
                ? "bg-purple-500/20 text-purple-300 font-bold border border-purple-500/30"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Test 2 Split (9,732)
          </button>
          <button
            onClick={() => setActiveSplit("val")}
            className={`px-3 py-1.5 rounded transition-colors font-mono ${
              activeSplit === "val"
                ? "bg-purple-500/20 text-purple-300 font-bold border border-purple-500/30"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Validation Split (1,625)
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-amber-950/40 border border-amber-800/80 text-amber-300 rounded-xl p-4 text-xs">
          {error}
        </div>
      )}

      {/* Model Inventory Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-900 border border-purple-900/40 rounded-xl p-5">
          <div className="flex items-center gap-2 text-purple-400 text-xs font-semibold uppercase tracking-wider mb-2">
            <Cpu className="w-4 h-4" /> Classifier
          </div>
          <h3 className="font-bold text-sm text-slate-100">Future Occupancy</h3>
          <p className="text-xs text-slate-400 mt-1">
            RandomForestClassifier (100 trees, max depth 12). Predicts binary room presence at <code className="text-purple-300">t+10m</code>.
          </p>
          <div className="mt-4 pt-3 border-t border-slate-800 flex justify-between text-xs font-mono">
            <span className="text-slate-400">{activeSplit.toUpperCase()} Accuracy:</span>
            <span className="text-emerald-400 font-bold">
              {formatPercent(occupancyModel?.accuracy)}
            </span>
          </div>
          <div className="mt-1 flex justify-between text-xs font-mono text-slate-400">
            <span>ROC-AUC:</span>
            <span className="text-slate-200">{formatMetricScore(occupancyModel?.roc_auc)}</span>
          </div>
        </div>

        <div className="bg-slate-900 border border-sky-900/40 rounded-xl p-5">
          <div className="flex items-center gap-2 text-sky-400 text-xs font-semibold uppercase tracking-wider mb-2">
            <LineChart className="w-4 h-4" /> Regressor
          </div>
          <h3 className="font-bold text-sm text-slate-100">Future Temperature</h3>
          <p className="text-xs text-slate-400 mt-1">
            GradientBoostingRegressor (lr=0.08, depth 4). Forecasts room thermal trajectory at <code className="text-sky-300">t+10m</code>.
          </p>
          <div className="mt-4 pt-3 border-t border-slate-800 flex justify-between text-xs font-mono">
            <span className="text-slate-400">{activeSplit.toUpperCase()} MAE:</span>
            <span className="text-sky-400 font-bold">
              {tempModel?.mae !== undefined ? `${tempModel.mae.toFixed(3)} °C` : "--"}
            </span>
          </div>
          <div className="mt-1 flex justify-between text-xs font-mono text-slate-400">
            <span>R² Score:</span>
            <span className="text-slate-200">{formatMetricScore(tempModel?.r2)}</span>
          </div>
        </div>

        <div className="bg-slate-900 border border-indigo-900/40 rounded-xl p-5">
          <div className="flex items-center gap-2 text-indigo-400 text-xs font-semibold uppercase tracking-wider mb-2">
            <Target className="w-4 h-4" /> Regressor
          </div>
          <h3 className="font-bold text-sm text-slate-100">Future Humidity</h3>
          <p className="text-xs text-slate-400 mt-1">
            Ridge Regressor (L2 alpha=10.0). Linear baseline forecaster for ambient moisture at <code className="text-indigo-300">t+10m</code>.
          </p>
          <div className="mt-4 pt-3 border-t border-slate-800 flex justify-between text-xs font-mono">
            <span className="text-slate-400">{activeSplit.toUpperCase()} MAE:</span>
            <span className="text-indigo-400 font-bold">
              {humidityModel?.mae !== undefined ? `${humidityModel.mae.toFixed(3)} %` : "--"}
            </span>
          </div>
          <div className="mt-1 flex justify-between text-xs font-mono text-slate-400">
            <span>R² Score:</span>
            <span className="text-slate-200">{formatMetricScore(humidityModel?.r2)}</span>
          </div>
        </div>
      </div>

      {/* Confusion Matrix Visualizer */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <ConfusionMatrixCard
          tn={cm?.tn}
          fp={cm?.fp}
          fn={cm?.fn}
          tp={cm?.tp}
          accuracy={occupancyModel?.accuracy}
          precision={occupancyModel?.precision}
          recall={occupancyModel?.recall}
          f1={occupancyModel?.f1}
          rocAuc={occupancyModel?.roc_auc}
          splitName={activeSplit === "test2" ? "Test 2 Partition (9,732 samples)" : "Validation Partition (1,625 samples)"}
        />

        {/* Feature Importance Leaderboard */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm text-xs">
          <h3 className="text-sm font-semibold text-slate-100 mb-1">
            RandomForest Feature Importances
          </h3>
          <p className="text-slate-400 text-xs mb-4">
            Relative contribution of top engineered features ({modelsInfo?.total_features || 50} total non-leaking features).
          </p>

          <div className="space-y-3 font-mono">
            {[
              { name: "Light_roll_mean_15m", score: 0.241, label: "Ambient light 15-min rolling average" },
              { name: "CO2_roll_mean_15m", score: 0.187, label: "CO2 15-min rolling average" },
              { name: "Light (Instantaneous)", score: 0.134, label: "Instantaneous lux observation" },
              { name: "CO2 (Instantaneous)", score: 0.092, label: "Instantaneous CO2 reading" },
              { name: "Temperature_diff_10m", score: 0.068, label: "10-minute rate of change in temperature" },
              { name: "hour", score: 0.051, label: "Diurnal hour of the day" },
              { name: "sin_time / cos_time", score: 0.043, label: "Cyclical time-of-day encoding" },
            ].map((f) => (
              <div key={f.name}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-200">{f.name}</span>
                  <span className="text-purple-400 font-bold">{(f.score * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-slate-950 rounded-full h-1.5 overflow-hidden border border-slate-800">
                  <div
                    className="bg-purple-500 h-1.5 rounded-full"
                    style={{ width: `${f.score * 100 * 3}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
