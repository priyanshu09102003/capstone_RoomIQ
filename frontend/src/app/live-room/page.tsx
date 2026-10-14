"use client";

import React, { useState, useEffect } from "react";
import {
  Compass,
  Droplets,
  Gauge,
  RotateCcw,
  StepForward,
  Sun,
  Thermometer,
  Wind,
} from "lucide-react";
import { api } from "@/lib/api";
import { SimulationStepResult, SimulationStateSummary } from "@/types/api";
import { ConnectionAlert } from "@/components/common/ConnectionAlert";
import { MetricCard } from "@/components/common/MetricCard";
import { RetrospectiveCard } from "@/components/inference/RetrospectiveCard";
import { ApplianceTile } from "@/components/common/ApplianceTile";
import { StatusBadge } from "@/components/common/StatusBadge";
import { formatTimestamp } from "@/lib/formatters";

export default function LiveRoomPage() {
  const [stepData, setStepData] = useState<SimulationStepResult | null>(null);
  const [summary, setSummary] = useState<SimulationStateSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch initial simulation status on mount to populate current sensor and appliance state
  useEffect(() => {
    let mounted = true;
    const fetchStatus = async () => {
      try {
        const res = await api.getSimulationStatus();
        if (mounted) setSummary(res);
      } catch (err: unknown) {
        if (mounted && err instanceof Error) {
          setError(err.message);
        }
      }
    };
    fetchStatus();
    return () => {
      mounted = false;
    };
  }, []);

  const handleStep = async () => {
    if (loading) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.stepSimulation();
      setStepData(res);
      // Also refresh summary state
      const updatedSummary = await api.getSimulationStatus();
      setSummary(updatedSummary);
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    if (loading) return;
    setLoading(true);
    setError(null);
    try {
      await api.resetSimulation();
      setStepData(null);
      const updatedSummary = await api.getSimulationStatus();
      setSummary(updatedSummary);
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const snapshot = stepData?.sensor_snapshot || summary?.latest_record;
  const retro = stepData?.retrospective_evaluation;
  const futureTruth = stepData?.future_ground_truth;
  const appliance = stepData?.appliance_state || summary?.appliance_state || { fan_on: false, light_on: false };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <ConnectionAlert />

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-wrap items-center justify-between gap-4 shadow-sm">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-xl font-bold text-slate-100">
              Live Replay Snapshot & Retrospective Auditing
            </h1>
            <StatusBadge status={stepData ? "ACTIVE" : "AWAITING STEP"} size="sm" />
          </div>
          <p className="text-xs text-slate-400">
            Current sequential observation from <code className="text-sky-400 font-mono">test2_clean.csv</code> —{" "}
            {stepData
              ? `Step Index ${stepData.step_index} | ${formatTimestamp(stepData.timestamp)}`
              : "Execute single step to load snapshot and issue 10-minute ML forecast"}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleStep}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs transition-colors disabled:opacity-50 shadow-sm shadow-sky-500/20"
          >
            <StepForward className="w-3.5 h-3.5" />
            {loading ? "Stepping..." : "Step 1 Min Forward"}
          </button>
          <button
            onClick={handleReset}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-colors disabled:opacity-50"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reset
          </button>
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

      {/* Instantaneous Sensor Gauges */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        <MetricCard
          title="Instantaneous Temp"
          value={snapshot ? snapshot.temperature : null}
          unit="°C"
          icon={<Thermometer className="w-4 h-4" />}
          subtitle="ASHRAE 55 Target"
          accentColor="cyan"
        />

        <MetricCard
          title="Instantaneous Humidity"
          value={snapshot ? snapshot.humidity : null}
          unit="%"
          icon={<Droplets className="w-4 h-4" />}
          subtitle="Relative Humidity"
          accentColor="cyan"
        />

        <MetricCard
          title="Recorded Light"
          value={snapshot ? snapshot.light : null}
          unit="Lux"
          icon={<Sun className="w-4 h-4" />}
          subtitle="Ambient Sensor"
          accentColor="amber"
        />

        <MetricCard
          title="Recorded CO2"
          value={snapshot ? snapshot.co2 : null}
          unit="ppm"
          icon={<Wind className="w-4 h-4" />}
          subtitle="Carbon Dioxide"
          accentColor="emerald"
        />

        <MetricCard
          title="Humidity Ratio"
          value={snapshot ? snapshot.humidity_ratio : null}
          unit="kg/kg"
          icon={<Gauge className="w-4 h-4" />}
          subtitle="Enthalpy Factor"
          accentColor="purple"
        />
      </div>

      {/* Virtual Appliance Actuators */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <ApplianceTile
          device="fan"
          state={appliance.fan_on}
          reason={
            stepData?.transition_events?.find((e) => e.device === "fan")?.decision_reason ||
            (appliance.fan_on
              ? "Maintaining ON within hysteresis band."
              : "Forecast temperature below ON threshold.")
          }
          lastSwitchedAt={appliance.fan_last_switched_at}
          parameterNote="Hysteresis Controlled (300s lock)"
        />

        <ApplianceTile
          device="light"
          state={appliance.light_on}
          reason={
            stepData?.transition_events?.find((e) => e.device === "light")?.decision_reason ||
            (appliance.light_on
              ? "Occupied and ambient light below threshold."
              : "Room predicted vacant; light OFF.")
          }
          lastSwitchedAt={appliance.light_last_switched_at}
          parameterNote="Vacancy delay & Lux threshold"
        />
      </div>

      {/* Retrospective Auditing & Future Ground Truth Isolation */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <RetrospectiveCard
          retro={retro}
          futureGroundTruth={futureTruth}
        />

        {/* Dynamic Slicing Explanation */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-3">
          <div className="flex items-center gap-2">
            <Compass className="w-4 h-4 text-sky-400" />
            <h3 className="font-semibold text-slate-100">
              Zero-Leakage Replay Principles
            </h3>
          </div>

          <p className="text-slate-400 leading-relaxed text-xs">
            At step index <code className="text-sky-300 font-mono">{stepData ? stepData.step_index : "k"}</code>, the feature window is dynamically sliced to only include records <code className="text-slate-300 font-mono">df.iloc[max(0, k-25) : k+1]</code>.
          </p>

          <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-3 space-y-2 text-[11px] font-mono">
            <div className="text-emerald-400 flex items-center gap-1.5">
              <span>✓ Past observations (≤ k):</span>
              <span className="text-slate-300">Feature engineering input</span>
            </div>
            <div className="text-rose-400 flex items-center gap-1.5">
              <span>✕ Future observations (&gt; k):</span>
              <span className="text-slate-300">Strictly excluded from predictor</span>
            </div>
            <div className="text-purple-400 flex items-center gap-1.5">
              <span>◎ Forecast target (k + 10m):</span>
              <span className="text-slate-300">Enqueued for retrospective audit</span>
            </div>
          </div>

          <p className="text-slate-500 italic text-[11px]">
            When the simulation advances 10 steps, the enqueued prediction is dequeued and verified against the arrival observation.
          </p>
        </div>
      </div>
    </div>
  );
}
