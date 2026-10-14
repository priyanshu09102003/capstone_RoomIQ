"use client";

import React, { useState, useEffect } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import { BarChart2 } from "lucide-react";

export interface SensorPoint {
  time: string;
  temperature: number;
  forecastTemperature?: number;
  humidity: number;
  forecastHumidity?: number;
  light: number;
  co2: number;
}

interface SensorTrendChartProps {
  data: SensorPoint[];
}

export function SensorTrendChart({ data }: SensorTrendChartProps) {
  const [mounted, setMounted] = useState(false);
  const [activeSensors, setActiveSensors] = useState({
    temperature: true,
    humidity: true,
    forecast: true,
    light: false,
    co2: false,
  });

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center text-xs h-72 flex items-center justify-center text-slate-500 font-mono">
        Initializing telemetry renderer...
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center text-xs">
        <BarChart2 className="w-8 h-8 mx-auto text-slate-600 mb-2" />
        <h4 className="font-semibold text-slate-300">No Telemetry Streamed Yet</h4>
        <p className="text-slate-500 mt-1 max-w-sm mx-auto">
          Execute single steps or stream 5 steps to collect chronological sensor telemetry and 10-minute ML forecasts.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-100">
            Chronological Telemetry Stream
          </h3>
          <p className="text-xs text-slate-400">
            Real-time sensory timeline ({data.length} buffered points)
          </p>
        </div>

        {/* Sensor & Forecast Visibility Toggles */}
        <div className="flex flex-wrap gap-2 text-xs">
          <button
            onClick={() =>
              setActiveSensors((s) => ({ ...s, temperature: !s.temperature }))
            }
            className={`px-2.5 py-1 rounded-md border font-mono transition-colors ${
              activeSensors.temperature
                ? "bg-sky-500/10 text-sky-400 border-sky-500/30"
                : "bg-slate-950 text-slate-500 border-slate-800"
            }`}
          >
            Temp (°C)
          </button>
          <button
            onClick={() =>
              setActiveSensors((s) => ({ ...s, humidity: !s.humidity }))
            }
            className={`px-2.5 py-1 rounded-md border font-mono transition-colors ${
              activeSensors.humidity
                ? "bg-indigo-500/10 text-indigo-400 border-indigo-500/30"
                : "bg-slate-950 text-slate-500 border-slate-800"
            }`}
          >
            Humidity (%)
          </button>
          <button
            onClick={() =>
              setActiveSensors((s) => ({ ...s, forecast: !s.forecast }))
            }
            className={`px-2.5 py-1 rounded-md border font-mono transition-colors ${
              activeSensors.forecast
                ? "bg-purple-500/10 text-purple-400 border-purple-500/30 font-bold"
                : "bg-slate-950 text-slate-500 border-slate-800"
            }`}
          >
            Forecast Trajectory (t+10m)
          </button>
          <button
            onClick={() =>
              setActiveSensors((s) => ({ ...s, light: !s.light }))
            }
            className={`px-2.5 py-1 rounded-md border font-mono transition-colors ${
              activeSensors.light
                ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                : "bg-slate-950 text-slate-500 border-slate-800"
            }`}
          >
            Light (Lux)
          </button>
          <button
            onClick={() =>
              setActiveSensors((s) => ({ ...s, co2: !s.co2 }))
            }
            className={`px-2.5 py-1 rounded-md border font-mono transition-colors ${
              activeSensors.co2
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                : "bg-slate-950 text-slate-500 border-slate-800"
            }`}
          >
            CO2 (ppm)
          </button>
        </div>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="time" stroke="#64748b" fontSize={11} />
            <YAxis stroke="#64748b" fontSize={11} domain={["auto", "auto"]} />
            <Tooltip
              contentStyle={{
                backgroundColor: "#090d16",
                borderColor: "#1e293b",
                borderRadius: "0.5rem",
                fontSize: "12px",
              }}
            />
            {activeSensors.temperature && (
              <Line
                type="monotone"
                dataKey="temperature"
                stroke="#38bdf8"
                strokeWidth={2}
                dot={false}
                name="Temperature (°C)"
              />
            )}
            {activeSensors.forecast && (
              <Line
                type="monotone"
                dataKey="forecastTemperature"
                stroke="#0284c7"
                strokeWidth={2}
                strokeDasharray="4 4"
                dot={false}
                name="Forecast Temp (°C)"
              />
            )}
            {activeSensors.humidity && (
              <Line
                type="monotone"
                dataKey="humidity"
                stroke="#818cf8"
                strokeWidth={2}
                dot={false}
                name="Humidity (%)"
              />
            )}
            {activeSensors.forecast && (
              <Line
                type="monotone"
                dataKey="forecastHumidity"
                stroke="#c084fc"
                strokeWidth={2}
                strokeDasharray="4 4"
                dot={false}
                name="Forecast Humidity (%)"
              />
            )}
            {activeSensors.light && (
              <Line
                type="monotone"
                dataKey="light"
                stroke="#fbbf24"
                strokeWidth={2}
                dot={false}
                name="Light (Lux)"
              />
            )}
            {activeSensors.co2 && (
              <Line
                type="monotone"
                dataKey="co2"
                stroke="#34d399"
                strokeWidth={2}
                dot={false}
                name="CO2 (ppm)"
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
