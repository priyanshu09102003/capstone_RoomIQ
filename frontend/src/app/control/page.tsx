"use client";

import React, { useEffect, useState } from "react";
import { AlertCircle, CheckCircle, Fan, Lightbulb, RotateCcw, Save, Sliders } from "lucide-react";
import { api } from "@/lib/api";
import { ControlConfig } from "@/types/api";
import { ConnectionAlert } from "@/components/common/ConnectionAlert";

const DEFAULT_CONFIG: ControlConfig = {
  fan_temp_on_threshold: 22.5,
  fan_temp_off_threshold: 21.5,
  fan_min_switching_interval_seconds: 300,
  light_lux_threshold: 250.0,
  light_vacancy_delay_seconds: 300,
};

export default function ControlPage() {
  const [config, setConfig] = useState<ControlConfig>(DEFAULT_CONFIG);
  const [speed, setSpeed] = useState<number>(1.0);
  const [saving, setSaving] = useState(false);
  const [statusMsg, setStatusMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    const loadConfig = async () => {
      try {
        const res = await api.getConfig();
        setConfig(res.control_config);
        setSpeed(res.playback_speed);
      } catch (err: unknown) {
        if (err instanceof Error) {
          setStatusMsg({ type: "error", text: `Could not load backend policy config: ${err.message}` });
        }
      }
    };
    loadConfig();
  }, []);

  const hysteresisError =
    config.fan_temp_off_threshold >= config.fan_temp_on_threshold
      ? `Lower threshold (${config.fan_temp_off_threshold}°C) must be strictly less than upper threshold (${config.fan_temp_on_threshold}°C) to maintain hysteresis.`
      : null;

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (hysteresisError) return;

    setSaving(true);
    setStatusMsg(null);
    try {
      const res = await api.updateConfig({
        ...config,
        playback_speed: speed,
      });
      setConfig(res.control_config);
      setSpeed(res.playback_speed);
      setStatusMsg({ type: "success", text: "Control policy successfully updated in FastAPI backend." });
    } catch (err: unknown) {
      if (err instanceof Error) {
        setStatusMsg({ type: "error", text: err.message });
      } else {
        setStatusMsg({ type: "error", text: "Failed to update configuration." });
      }
    } finally {
      setSaving(false);
    }
  };

  const handleResetDefaults = async () => {
    setConfig(DEFAULT_CONFIG);
    setSpeed(1.0);
    setStatusMsg(null);
    try {
      await api.updateConfig({
        ...DEFAULT_CONFIG,
        playback_speed: 1.0,
      });
      setStatusMsg({ type: "success", text: "Restored demonstration heuristic defaults." });
    } catch (err: unknown) {
      if (err instanceof Error) {
        setStatusMsg({ type: "error", text: `Could not reset backend policy config: ${err.message}` });
      }
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <ConnectionAlert />

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex items-center gap-2 mb-1">
          <Sliders className="w-5 h-5 text-sky-400" />
          <h1 className="text-xl font-bold text-slate-100">
            Virtual Automation Policy Configuration
          </h1>
        </div>
        <p className="text-xs text-slate-400">
          Configure temperature hysteresis bands, anti-short-cycling intervals, and occupancy vacancy hold timers in the Python decision engine.
        </p>
      </div>

      {statusMsg && (
        <div
          className={`rounded-xl p-4 text-xs flex items-center justify-between border ${
            statusMsg.type === "success"
              ? "bg-emerald-950/40 border-emerald-800 text-emerald-300"
              : "bg-rose-950/40 border-rose-800 text-rose-300"
          }`}
        >
          <div className="flex items-center gap-2">
            {statusMsg.type === "success" ? (
              <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            )}
            <span>{statusMsg.text}</span>
          </div>
          <button
            onClick={() => setStatusMsg(null)}
            className="text-[11px] underline opacity-80 hover:opacity-100 ml-3"
          >
            Dismiss
          </button>
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Fan Automation Policy */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center gap-2.5 pb-3 border-b border-slate-800">
            <div className="w-7 h-7 rounded-lg bg-sky-500/10 border border-sky-500/30 text-sky-400 flex items-center justify-center">
              <Fan className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-100">
                Virtual Fan Actuator (Thermal Hysteresis)
              </h2>
              <span className="text-[11px] text-slate-400">
                Driven by 10-minute forecast temperature and hysteresis band logic.
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-300 font-medium mb-1.5 text-xs">
                Upper Threshold — Fan ON (°C)
              </label>
              <input
                type="number"
                step="0.1"
                value={config.fan_temp_on_threshold}
                onChange={(e) =>
                  setConfig({ ...config, fan_temp_on_threshold: parseFloat(e.target.value) || 0 })
                }
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 font-mono text-xs focus:outline-none focus:border-sky-500 transition-colors"
              />
              <span className="text-[11px] text-slate-500 mt-1 block">
                Triggers fan ON when forecast temp &gt; this value (default 22.5°C).
              </span>
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1.5 text-xs">
                Lower Threshold — Fan OFF (°C)
              </label>
              <input
                type="number"
                step="0.1"
                value={config.fan_temp_off_threshold}
                onChange={(e) =>
                  setConfig({ ...config, fan_temp_off_threshold: parseFloat(e.target.value) || 0 })
                }
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 font-mono text-xs focus:outline-none focus:border-sky-500 transition-colors"
              />
              <span className="text-[11px] text-slate-500 mt-1 block">
                Triggers fan OFF when forecast temp ≤ this value (default 21.5°C).
              </span>
            </div>
          </div>

          {hysteresisError && (
            <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-800/80 text-rose-300 text-xs">
              {hysteresisError}
            </div>
          )}

          <div>
            <label className="block text-slate-300 font-medium mb-1.5 text-xs">
              Minimum Switching Interval (Seconds)
            </label>
            <input
              type="number"
              min="0"
              step="30"
              value={config.fan_min_switching_interval_seconds}
              onChange={(e) =>
                setConfig({
                  ...config,
                  fan_min_switching_interval_seconds: parseInt(e.target.value) || 0,
                })
              }
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 font-mono text-xs focus:outline-none focus:border-sky-500 transition-colors max-w-sm"
            />
            <span className="text-[11px] text-slate-500 mt-1 block">
              Enforces a minimum duration between consecutive state toggles to prevent short-cycling.
            </span>
          </div>
        </div>

        {/* Light Automation Policy */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center gap-2.5 pb-3 border-b border-slate-800">
            <div className="w-7 h-7 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 flex items-center justify-center">
              <Lightbulb className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-100">
                Virtual Light Actuator (Ambient Lux & Vacancy Delay)
              </h2>
              <span className="text-[11px] text-slate-400">
                Driven by predicted room presence, ambient light (Lux), and vacancy hold timers.
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-300 font-medium mb-1.5 text-xs">
                Ambient Light Threshold (Lux)
              </label>
              <input
                type="number"
                min="0"
                step="10"
                value={config.light_lux_threshold}
                onChange={(e) =>
                  setConfig({ ...config, light_lux_threshold: parseFloat(e.target.value) || 0 })
                }
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 font-mono text-xs focus:outline-none focus:border-sky-500 transition-colors"
              />
              <span className="text-[11px] text-slate-500 mt-1 block">
                If room is occupied and recorded light is below this value, light switches ON.
              </span>
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1.5 text-xs">
                Vacancy Delay (Seconds)
              </label>
              <input
                type="number"
                min="0"
                step="30"
                value={config.light_vacancy_delay_seconds}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    light_vacancy_delay_seconds: parseInt(e.target.value) || 0,
                  })
                }
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 font-mono text-xs focus:outline-none focus:border-sky-500 transition-colors"
              />
              <span className="text-[11px] text-slate-500 mt-1 block">
                Duration to hold light ON after room is forecast vacant before switching OFF.
              </span>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center justify-between gap-4 pt-2">
          <button
            type="button"
            onClick={handleResetDefaults}
            disabled={saving}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs border border-slate-700 transition-colors disabled:opacity-50"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reset to Demonstration Defaults
          </button>

          <button
            type="submit"
            disabled={saving || Boolean(hysteresisError)}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs transition-colors disabled:opacity-50 shadow-md shadow-sky-500/20"
          >
            <Save className="w-4 h-4" />
            {saving ? "Updating Backend..." : "Save Policy Configuration"}
          </button>
        </div>
      </form>
    </div>
  );
}
