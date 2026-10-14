"use client";

import React, { useState } from "react";
import { BarChart3, FastForward, RotateCcw, StepForward } from "lucide-react";
import { api } from "@/lib/api";
import { ConnectionAlert } from "@/components/common/ConnectionAlert";
import { SensorTrendChart, SensorPoint } from "@/components/charts/SensorTrendChart";
import { formatTimeOnly } from "@/lib/formatters";

export default function AnalyticsPage() {
  const [dataPoints, setDataPoints] = useState<SensorPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleStep = async () => {
    if (loading) return;
    setLoading(true);
    setError(null);
    try {
      const step = await api.stepSimulation();
      const s = step.sensor_snapshot;
      const pred = step.prediction;
      const point: SensorPoint = {
        time: formatTimeOnly(s.timestamp),
        temperature: Number(s.temperature.toFixed(2)),
        forecastTemperature: Number(pred.forecast_temperature.toFixed(2)),
        humidity: Number(s.humidity.toFixed(2)),
        forecastHumidity: Number(pred.forecast_humidity.toFixed(2)),
        light: Number(s.light.toFixed(1)),
        co2: Number(s.co2.toFixed(1)),
      };
      setDataPoints((prev) => [...prev.slice(-40), point]);
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleBatchStream = async () => {
    if (loading) return;
    setLoading(true);
    setError(null);
    try {
      const steps = await api.batchStep(5);
      const points: SensorPoint[] = steps.map((st) => ({
        time: formatTimeOnly(st.sensor_snapshot.timestamp),
        temperature: Number(st.sensor_snapshot.temperature.toFixed(2)),
        forecastTemperature: Number(st.prediction.forecast_temperature.toFixed(2)),
        humidity: Number(st.sensor_snapshot.humidity.toFixed(2)),
        forecastHumidity: Number(st.prediction.forecast_humidity.toFixed(2)),
        light: Number(st.sensor_snapshot.light.toFixed(1)),
        co2: Number(st.sensor_snapshot.co2.toFixed(1)),
      }));
      setDataPoints((prev) => [...prev.slice(-40 + points.length), ...points]);
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setDataPoints([]);
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <ConnectionAlert />

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-wrap items-center justify-between gap-4 shadow-sm">
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-sky-400" />
            Sensor Telemetry & Forecast Trends
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Streaming observation telemetry and 10-minute forecast trajectories ({dataPoints.length} points buffered).
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleStep}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs transition-colors disabled:opacity-50 shadow-sm shadow-sky-500/20"
          >
            <StepForward className="w-3.5 h-3.5" />
            {loading ? "Streaming..." : "Stream 1 Step"}
          </button>

          <button
            onClick={handleBatchStream}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-purple-500 hover:bg-purple-400 text-slate-950 font-bold text-xs transition-colors disabled:opacity-50 shadow-sm shadow-purple-500/20"
          >
            <FastForward className="w-3.5 h-3.5" />
            {loading ? "Streaming 5..." : "Stream 5 Steps"}
          </button>

          {dataPoints.length > 0 && (
            <button
              onClick={handleClear}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs border border-slate-700 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Clear
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-amber-950/40 border border-amber-800/80 text-amber-300 rounded-xl p-4 text-xs flex items-center justify-between">
          <span>{error}</span>
          <button
            onClick={() => setError(null)}
            className="text-amber-400 hover:text-amber-200 text-[11px] underline ml-3"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Real-time Recharts Component with Forecast Series */}
      <SensorTrendChart data={dataPoints} />

      {/* Sensor Distribution Summary Table (Benchmark findings from Phase 2A) */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm text-xs">
        <h3 className="text-sm font-semibold text-slate-100 mb-2">
          Dataset Statistical Profile (Phase 2A Audit Findings)
        </h3>
        <p className="text-slate-400 text-xs mb-4">
          Baseline distributions computed across all 20,560 raw observations across training, test, and test2 partitions.
        </p>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 text-[11px] uppercase">
                <th className="pb-2">Sensor Feature</th>
                <th className="pb-2">Mean</th>
                <th className="pb-2">Std Dev</th>
                <th className="pb-2">Min</th>
                <th className="pb-2">Max</th>
                <th className="pb-2">Physical Units</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300 text-[11px]">
              <tr>
                <td className="py-2.5 font-bold text-sky-400">Temperature</td>
                <td>20.91</td>
                <td>1.02</td>
                <td>19.00</td>
                <td>24.41</td>
                <td className="text-slate-500">°C</td>
              </tr>
              <tr>
                <td className="py-2.5 font-bold text-sky-400">Relative Humidity</td>
                <td>27.66</td>
                <td>4.98</td>
                <td>16.75</td>
                <td>39.50</td>
                <td className="text-slate-500">%</td>
              </tr>
              <tr>
                <td className="py-2.5 font-bold text-amber-400">Light</td>
                <td>130.76</td>
                <td>210.53</td>
                <td>0.00</td>
                <td>1697.25</td>
                <td className="text-slate-500">Lux</td>
              </tr>
              <tr>
                <td className="py-2.5 font-bold text-emerald-400">CO2</td>
                <td>683.93</td>
                <td>388.35</td>
                <td>412.75</td>
                <td>2076.50</td>
                <td className="text-slate-500">ppm</td>
              </tr>
              <tr>
                <td className="py-2.5 font-bold text-purple-400">Humidity Ratio</td>
                <td>0.0042</td>
                <td>0.0009</td>
                <td>0.0027</td>
                <td>0.0065</td>
                <td className="text-slate-500">kg/kg</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
