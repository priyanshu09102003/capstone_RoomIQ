"use client";

import React from "react";
import { BrainCircuit, Users, UserX, Thermometer, Droplets, Target } from "lucide-react";
import { PredictionPayload } from "@/types/api";

interface ForecastGaugeProps {
  prediction?: PredictionPayload | null;
  currentTemp?: number;
  currentHumidity?: number;
}

export function ForecastGauge({
  prediction,
  currentTemp,
  currentHumidity,
}: ForecastGaugeProps) {
  if (!prediction) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm text-center">
        <div className="w-10 h-10 rounded-xl bg-purple-950/60 border border-purple-800/40 text-purple-400 flex items-center justify-center mx-auto mb-3">
          <BrainCircuit className="w-5 h-5" />
        </div>
        <h3 className="text-sm font-semibold text-slate-200">10-Minute Predictive Horizon</h3>
        <p className="text-xs text-slate-500 mt-1 italic">
          No active prediction. Execute a step or connect the backend service.
        </p>
      </div>
    );
  }

  const isOccupied = prediction.predicted_occupancy === 1;
  const probPercent = Math.round(prediction.occupancy_probability * 100);

  const tempDelta =
    currentTemp !== undefined
      ? (prediction.forecast_temperature - currentTemp).toFixed(2)
      : null;
  const humidityDelta =
    currentHumidity !== undefined
      ? (prediction.forecast_humidity - currentHumidity).toFixed(2)
      : null;

  return (
    <div className="bg-slate-900 border border-purple-900/40 rounded-xl p-5 shadow-sm shadow-purple-950/20">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
            <BrainCircuit className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-100">
              10-Minute Machine Learning Forecast
            </h3>
            <span className="text-[10px] text-purple-400 font-mono">
              TARGET HORIZON: t+10m
            </span>
          </div>
        </div>

        <span
          className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border tracking-wider ${
            isOccupied
              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
              : "bg-slate-800 text-slate-300 border-slate-700/60"
          }`}
        >
          {isOccupied ? (
            <>
              <Users className="w-3.5 h-3.5" /> OCCUPIED
            </>
          ) : (
            <>
              <UserX className="w-3.5 h-3.5" /> VACANT
            </>
          )}
        </span>
      </div>

      {/* Confidence Bar */}
      <div className="mb-4 bg-slate-950/60 border border-slate-800/80 rounded-lg p-3">
        <div className="flex justify-between items-center text-xs mb-1.5">
          <span className="text-slate-400 flex items-center gap-1">
            <Target className="w-3 h-3 text-purple-400" />
            Occupancy Probability Confidence:
          </span>
          <span className="font-mono font-bold text-slate-200">{probPercent}%</span>
        </div>
        <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800">
          <div
            className={`h-2 rounded-full transition-all duration-300 ${
              isOccupied ? "bg-emerald-400" : "bg-slate-600"
            }`}
            style={{ width: `${probPercent}%` }}
          />
        </div>
      </div>

      {/* Numerical Regressors */}
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3">
          <div className="flex items-center gap-1.5 text-slate-400 mb-1">
            <Thermometer className="w-3.5 h-3.5 text-sky-400" />
            <span>Forecast Temp</span>
          </div>
          <div className="flex items-baseline gap-1 font-mono">
            <span className="text-lg font-bold text-slate-100">
              {prediction.forecast_temperature.toFixed(2)}
            </span>
            <span className="text-slate-500">°C</span>
            {tempDelta && (
              <span
                className={`ml-1 text-[10px] font-bold ${
                  Number(tempDelta) >= 0 ? "text-amber-400" : "text-sky-400"
                }`}
              >
                ({Number(tempDelta) >= 0 ? `+${tempDelta}` : tempDelta}°)
              </span>
            )}
          </div>
        </div>

        <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3">
          <div className="flex items-center gap-1.5 text-slate-400 mb-1">
            <Droplets className="w-3.5 h-3.5 text-sky-400" />
            <span>Forecast Humidity</span>
          </div>
          <div className="flex items-baseline gap-1 font-mono">
            <span className="text-lg font-bold text-slate-100">
              {prediction.forecast_humidity.toFixed(2)}
            </span>
            <span className="text-slate-500">%</span>
            {humidityDelta && (
              <span
                className={`ml-1 text-[10px] font-bold ${
                  Number(humidityDelta) >= 0 ? "text-sky-400" : "text-amber-400"
                }`}
              >
                ({Number(humidityDelta) >= 0 ? `+${humidityDelta}` : humidityDelta}%)
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
