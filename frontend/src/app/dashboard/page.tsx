"use client";

import React, { useEffect, useState } from "react";
import {
  Activity,
  Droplets,
  Gauge,
  RotateCcw,
  StepForward,
  Sun,
  Thermometer,
  Wind,
} from "lucide-react";
import { api } from "@/lib/api";
import {
  ApplianceState,
  PredictionPayload,
  SensorSnapshot,
  SimulationStateSummary,
  SimulationStepResult,
  TransitionEvent,
} from "@/types/api";
import { ConnectionAlert } from "@/components/common/ConnectionAlert";
import { MetricCard } from "@/components/common/MetricCard";
import { ApplianceTile } from "@/components/common/ApplianceTile";
import { ForecastGauge } from "@/components/inference/ForecastGauge";
import { StatusBadge } from "@/components/common/StatusBadge";
import { formatTimestamp, formatTimeOnly } from "@/lib/formatters";

export default function DashboardPage() {
  const [summary, setSummary] = useState<SimulationStateSummary | null>(null);
  const [lastStep, setLastStep] = useState<SimulationStepResult | null>(null);
  const [events, setEvents] = useState<TransitionEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setError(null);
      const s = await api.getSimulationStatus();
      setSummary(s);
      const ev = await api.getEvents(5);
      setEvents(ev.events);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Could not connect to FastAPI backend on port 8000.");
      }
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(() => {
      api.getSimulationStatus()
        .then((s) => {
          setSummary(s);
          if (s.events_count !== events.length) {
            api.getEvents(5).then((ev) => setEvents(ev.events)).catch(() => {});
          }
        })
        .catch(() => {});
    }, 2000);
    return () => clearInterval(interval);
  }, [events.length]);

  const handleStep = async () => {
    if (loading) return;
    setLoading(true);
    setError(null);
    try {
      const stepRes = await api.stepSimulation();
      setLastStep(stepRes);
      await loadData();
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
      await loadData();
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const sensors: SensorSnapshot | undefined = lastStep?.sensor_snapshot;
  const prediction: PredictionPayload | undefined = lastStep?.prediction;
  const appliance: ApplianceState = summary?.appliance_state || {
    fan_on: false,
    light_on: false,
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <ConnectionAlert />

      {/* Top Header & Replay Quick Actions */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-wrap items-center justify-between gap-4 shadow-sm">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-xl font-bold text-slate-100">
              Room Intelligence Dashboard
            </h1>
            {summary && <StatusBadge status={summary.status} size="sm" />}
          </div>
          <p className="text-xs text-slate-400">
            Replaying benchmark sequence{" "}
            <code className="text-sky-400 font-mono">test2_clean.csv</code> —{" "}
            {summary
              ? `Record ${summary.current_index.toLocaleString()} of ${summary.total_records.toLocaleString()} (${formatTimestamp(
                  summary.current_timestamp
                )})`
              : "Awaiting backend connection"}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleStep}
            disabled={loading || summary?.status === "RUNNING"}
            title={summary?.status === "RUNNING" ? "Pause replay before manual stepping" : undefined}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs transition-colors disabled:opacity-50 shadow-sm shadow-sky-500/20"
          >
            <StepForward className="w-3.5 h-3.5" />
            {loading ? "Stepping..." : "Step 1 Min"}
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

      {/* Sensor Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        <MetricCard
          title="Room Temperature"
          value={sensors ? sensors.temperature : null}
          unit="°C"
          icon={<Thermometer className="w-4 h-4" />}
          subtitle="Comfort target: 21.5-22.5°C"
          badge={sensors ? (sensors.temperature > 22.5 ? "Warm" : "Comfort") : undefined}
          accentColor="cyan"
        />

        <MetricCard
          title="Relative Humidity"
          value={sensors ? sensors.humidity : null}
          unit="%"
          icon={<Droplets className="w-4 h-4" />}
          subtitle="Target range: 30-50%"
          accentColor="cyan"
        />

        <MetricCard
          title="Ambient Light"
          value={sensors ? sensors.light : null}
          unit="Lux"
          icon={<Sun className="w-4 h-4" />}
          subtitle="Dark threshold: < 250 Lux"
          badge={sensors ? (sensors.light < 250 ? "Dark" : "Lit") : undefined}
          accentColor="amber"
        />

        <MetricCard
          title="Carbon Dioxide"
          value={sensors ? sensors.co2 : null}
          unit="ppm"
          icon={<Wind className="w-4 h-4" />}
          subtitle="Fresh air baseline: ~400 ppm"
          accentColor="emerald"
        />

        <MetricCard
          title="Humidity Ratio"
          value={sensors ? sensors.humidity_ratio : null}
          unit="kg/kg"
          icon={<Gauge className="w-4 h-4" />}
          subtitle="Psychrometric ratio"
          accentColor="purple"
        />
      </div>

      {/* Virtual Actuators & 10-Minute Forecast Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Fan & Light Actuators */}
        <div className="space-y-4 lg:col-span-1">
          <ApplianceTile
            device="fan"
            state={appliance.fan_on}
            reason={
              lastStep?.transition_events.find((e) => e.device === "fan")
                ?.decision_reason ||
              (appliance.fan_on
                ? "Maintaining ON within hysteresis band."
                : "Forecast temperature below ON threshold (22.50°C).")
            }
            lastSwitchedAt={appliance.fan_last_switched_at}
            parameterNote="Hysteresis: 21.5°C - 22.5°C (300s lock)"
          />

          <ApplianceTile
            device="light"
            state={appliance.light_on}
            reason={
              lastStep?.transition_events.find((e) => e.device === "light")
                ?.decision_reason ||
              (appliance.light_on
                ? "Occupied and ambient light below threshold."
                : "Room predicted vacant; light OFF.")
            }
            lastSwitchedAt={appliance.light_last_switched_at}
            parameterNote="Lux < 250 | Vacancy delay: 300s"
          />
        </div>

        {/* 10-Minute Horizon Forecast Card */}
        <div className="lg:col-span-2">
          <ForecastGauge
            prediction={prediction}
            currentTemp={sensors?.temperature}
            currentHumidity={sensors?.humidity}
          />

          {/* Recent Event Audit Preview */}
          <div className="mt-4 bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm text-xs">
            <h3 className="text-sm font-semibold text-slate-100 mb-2">
              Recent Virtual Actuation Switches
            </h3>
            {events.length > 0 ? (
              <div className="space-y-2 mt-3">
                {events.map((ev, i) => (
                  <div
                    key={i}
                    className="bg-slate-950/70 border border-slate-800 rounded-lg p-3 flex flex-wrap items-center justify-between gap-2"
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-bold uppercase tracking-wider text-slate-200">
                        {ev.device}
                      </span>
                      <span className="text-slate-400">
                        {ev.previous_state ? "ON" : "OFF"} →{" "}
                        <span className="font-bold text-sky-400">
                          {ev.new_state ? "ON" : "OFF"}
                        </span>
                      </span>
                    </div>
                    <p className="text-slate-400 text-[11px] flex-1 max-w-md">
                      {ev.decision_reason}
                    </p>
                    <span className="text-[10px] font-mono text-slate-500">
                      {formatTimeOnly(ev.timestamp)}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-500 italic mt-2">
                No appliance switches logged yet. Step the simulator forward through temperature or occupancy changes to observe transitions.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
