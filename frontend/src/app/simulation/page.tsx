"use client";

import React, { useEffect, useRef, useState } from "react";
import { PlaySquare, Database, Gauge, Clock, ShieldCheck, StepForward } from "lucide-react";
import { api } from "@/lib/api";
import { SimulationStateSummary, SimulationStepResult, SimulationStatus } from "@/types/api";
import { ConnectionAlert } from "@/components/common/ConnectionAlert";
import { PlaybackControls } from "@/components/simulation/PlaybackControls";
import { TimelineProgress } from "@/components/simulation/TimelineProgress";
import { MetricCard } from "@/components/common/MetricCard";
import { ApplianceTile } from "@/components/common/ApplianceTile";
import { formatTimestamp, formatTimeOnly } from "@/lib/formatters";

export default function SimulationPage() {
  const [summary, setSummary] = useState<SimulationStateSummary | null>(null);
  const [lastStep, setLastStep] = useState<SimulationStepResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const isPollingRef = useRef(false);

  const fetchStatus = async () => {
    if (isPollingRef.current) return;
    isPollingRef.current = true;
    try {
      const s = await api.getSimulationStatus();
      setSummary(s);
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
    } finally {
      isPollingRef.current = false;
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(() => {
      if (summary?.status === "RUNNING") {
        fetchStatus();
      }
    }, 1500);
    return () => clearInterval(interval);
  }, [summary?.status]);

  const handleStart = async () => {
    if (loading) return;
    setLoading(true);
    setError(null);
    try {
      await api.startSimulation();
      await fetchStatus();
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePause = async () => {
    if (loading) return;
    setLoading(true);
    setError(null);
    try {
      await api.pauseSimulation();
      await fetchStatus();
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleResume = async () => {
    if (loading) return;
    setLoading(true);
    setError(null);
    try {
      await api.resumeSimulation();
      await fetchStatus();
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
      setLastStep(null);
      await fetchStatus();
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleStep = async () => {
    if (loading || summary?.status === "RUNNING") return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.stepSimulation();
      setLastStep(res);
      await fetchStatus();
    } catch (err: unknown) {
      if (err instanceof Error) {
        if (err.message.includes("409") || err.message.includes("Conflict") || err.message.includes("continuous")) {
          setError("Continuous background replay is currently active. Pause the simulation before executing individual steps.");
        } else {
          setError(err.message);
        }
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSpeedChange = async (speed: number) => {
    try {
      await api.updateConfig({ playback_speed: speed });
      await fetchStatus();
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
    }
  };

  const status: SimulationStatus = summary?.status || "IDLE";
  const currentIndex = summary?.current_index ?? 10;
  const totalRecords = summary?.total_records ?? 9752;
  const currentTimestamp = summary?.current_timestamp;
  const playbackSpeed = summary?.playback_speed ?? 1.0;

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <ConnectionAlert />

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex items-center gap-2 mb-1">
          <PlaySquare className="w-5 h-5 text-sky-400" />
          <h1 className="text-xl font-bold text-slate-100">
            Deterministic Dataset Replay Simulator
          </h1>
        </div>
        <p className="text-xs text-slate-400">
          Chronological playback of cleaned sensor records from <code className="text-sky-300">test2_clean.csv</code> with zero future leakage.
        </p>
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

      {/* Replay Controls & Timeline Progress */}
      <PlaybackControls
        status={status}
        playbackSpeed={playbackSpeed}
        loading={loading}
        onStart={handleStart}
        onPause={handlePause}
        onResume={handleResume}
        onReset={handleReset}
        onStep={handleStep}
        onSpeedChange={handleSpeedChange}
      />

      <TimelineProgress
        currentIndex={currentIndex}
        totalRecords={totalRecords}
        currentTimestamp={currentTimestamp}
        status={status}
        splitName="test2 (9,752 records)"
      />

      {/* Step Result Telemetry (When stepped) */}
      {lastStep && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-200">
              Step {lastStep.step_index} Telemetry & Decisions ({formatTimestamp(lastStep.timestamp)})
            </h3>
            <span className="text-[11px] font-mono text-slate-400">
              Zero lookahead leakage enforced
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <MetricCard
              title="Recorded Temperature"
              value={lastStep.sensor_snapshot.temperature}
              unit="°C"
              icon={<Gauge className="w-4 h-4" />}
              subtitle={`10m Forecast: ${lastStep.prediction.forecast_temperature.toFixed(2)}°C`}
              accentColor="cyan"
            />
            <MetricCard
              title="Recorded Humidity"
              value={lastStep.sensor_snapshot.humidity}
              unit="%"
              icon={<Gauge className="w-4 h-4" />}
              subtitle={`10m Forecast: ${lastStep.prediction.forecast_humidity.toFixed(2)}%`}
              accentColor="cyan"
            />
            <MetricCard
              title="Ambient Light"
              value={lastStep.sensor_snapshot.light}
              unit="Lux"
              icon={<Gauge className="w-4 h-4" />}
              subtitle="Photo-sensor lux"
              accentColor="amber"
            />
            <MetricCard
              title="Forecast Occupancy"
              value={lastStep.prediction.predicted_occupancy === 1 ? "Occupied" : "Vacant"}
              unit=""
              icon={<ShieldCheck className="w-4 h-4" />}
              subtitle={`Confidence: ${(lastStep.prediction.occupancy_probability * 100).toFixed(1)}%`}
              accentColor="emerald"
            />
          </div>
        </div>
      )}
    </div>
  );
}
