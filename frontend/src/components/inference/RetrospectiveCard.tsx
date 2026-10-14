"use client";

import React from "react";
import { CheckCircle2, XCircle, Clock, ShieldCheck } from "lucide-react";
import { RetrospectiveComparison } from "@/types/api";

interface RetrospectiveCardProps {
  retro?: RetrospectiveComparison | null;
  futureGroundTruth?: Record<string, unknown> | null;
}

export function RetrospectiveCard({
  retro,
  futureGroundTruth,
}: RetrospectiveCardProps) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm text-xs">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-sky-400" />
          <h3 className="font-semibold text-slate-100">
            Retrospective Forecast Verification
          </h3>
        </div>
        <span className="text-[10px] text-slate-400 font-mono">
          EVALUATED AT ARRIVAL
        </span>
      </div>

      {retro ? (
        <div className="space-y-3">
          <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-400">Occupancy Prediction Accuracy:</span>
              <span
                className={`inline-flex items-center gap-1 font-bold ${
                  retro.occupancy_correct ? "text-emerald-400" : "text-rose-400"
                }`}
              >
                {retro.occupancy_correct ? (
                  <>
                    <CheckCircle2 className="w-3.5 h-3.5" /> ACCURATE
                  </>
                ) : (
                  <>
                    <XCircle className="w-3.5 h-3.5" /> MISMATCH
                  </>
                )}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400 font-mono">
              <div>Predicted: {retro.predicted_occupancy === 1 ? "Occupied" : "Vacant"}</div>
              <div>Actual Arrival: {retro.actual_occupancy === 1 ? "Occupied" : "Vacant"}</div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 font-mono">
            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-2.5">
              <div className="text-slate-400 text-[10px] mb-1">Temperature Error</div>
              <div className="text-sm font-bold text-slate-200">
                {retro.temperature_error > 0 ? `+${retro.temperature_error}` : retro.temperature_error}°C
              </div>
              <div className="text-[10px] text-slate-500">
                Pred: {retro.forecast_temperature.toFixed(2)} | Act: {retro.actual_temperature.toFixed(2)}
              </div>
            </div>

            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-2.5">
              <div className="text-slate-400 text-[10px] mb-1">Humidity Error</div>
              <div className="text-sm font-bold text-slate-200">
                {retro.humidity_error > 0 ? `+${retro.humidity_error}` : retro.humidity_error}%
              </div>
              <div className="text-[10px] text-slate-500">
                Pred: {retro.forecast_humidity.toFixed(2)} | Act: {retro.actual_humidity.toFixed(2)}
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-slate-950/40 border border-slate-800/60 rounded-lg p-3 text-center text-slate-500 italic">
          <Clock className="w-4 h-4 mx-auto mb-1 text-slate-600" />
          Retrospective evaluation is enqueued. First comparison matures after 10 consecutive simulation minutes.
        </div>
      )}

      {futureGroundTruth && (
        <div className="mt-3 pt-3 border-t border-slate-800/60 text-[11px] text-slate-400">
          <span className="font-semibold text-slate-300">Separate Future Ground Truth: </span>
          <span>
            Held in isolation for benchmark verification only. Never leaked to predictor.
          </span>
        </div>
      )}
    </div>
  );
}
