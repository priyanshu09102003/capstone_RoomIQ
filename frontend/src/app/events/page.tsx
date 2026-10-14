"use client";

import React, { useEffect, useState } from "react";
import { History, Fan, Lightbulb, Clock, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import { TransitionEvent } from "@/types/api";
import { ConnectionAlert } from "@/components/common/ConnectionAlert";
import { formatTimestamp, formatTemp, formatLux, formatCO2 } from "@/lib/formatters";

export default function EventsPage() {
  const [events, setEvents] = useState<TransitionEvent[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [deviceFilter, setDeviceFilter] = useState<string>("all");
  const [limit, setLimit] = useState<number>(50);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchEvents = async () => {
    setLoading(true);
    setError(null);
    try {
      const dev = deviceFilter === "all" ? undefined : deviceFilter;
      const res = await api.getEvents(limit, dev);
      setEvents(res.events);
      setTotalCount(res.total_count);
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, [deviceFilter, limit]);

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <ConnectionAlert />

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-wrap items-center justify-between gap-4 shadow-sm">
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <History className="w-5 h-5 text-sky-400" />
            Virtual Appliance Transition Audit Log
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Immutable log of state flips emitted by the RoomIQControlPolicy engine ({totalCount} total events recorded in current session).
          </p>
        </div>

        {/* Filter Controls */}
        <div className="flex items-center gap-2 text-xs">
          <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
            {["all", "fan", "light"].map((f) => (
              <button
                key={f}
                onClick={() => setDeviceFilter(f)}
                className={`px-3 py-1 rounded capitalize transition-colors ${
                  deviceFilter === f
                    ? "bg-sky-500/20 text-sky-400 font-bold border border-sky-500/30"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {f}
              </button>
            ))}
          </div>

          <button
            onClick={fetchEvents}
            disabled={loading}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors disabled:opacity-50"
            title="Refresh event log"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
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

      {/* Events Table / List */}
      {events.length > 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
          <div className="divide-y divide-slate-800/80">
            {events.map((ev, idx) => {
              const isFan = ev.device.toLowerCase() === "fan";
              return (
                <div key={idx} className="p-4 hover:bg-slate-800/30 transition-colors text-xs">
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2.5">
                      <div
                        className={`w-7 h-7 rounded-lg flex items-center justify-center border ${
                          isFan
                            ? "bg-cyan-950/80 text-cyan-400 border-cyan-800/60"
                            : "bg-amber-950/80 text-amber-400 border-amber-800/60"
                        }`}
                      >
                        {isFan ? <Fan className="w-4 h-4" /> : <Lightbulb className="w-4 h-4" />}
                      </div>

                      <span className="font-bold text-slate-200 uppercase tracking-wider">
                        {ev.device}
                      </span>

                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-950 border border-slate-800 text-slate-300">
                        {ev.previous_state ? "ON" : "OFF"} →{" "}
                        <span className={ev.new_state ? "text-emerald-400" : "text-rose-400"}>
                          {ev.new_state ? "ON" : "OFF"}
                        </span>
                      </span>
                    </div>

                    <span className="text-slate-400 font-mono text-[11px] flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-slate-400" />
                      {formatTimestamp(ev.timestamp)}
                    </span>
                  </div>

                  <p className="text-slate-300 text-xs leading-relaxed bg-slate-950/60 border border-slate-800/60 rounded-lg p-2.5">
                    {ev.decision_reason}
                  </p>

                  {ev.sensor_readings && (
                    <div className="mt-2 flex flex-wrap gap-3 font-mono text-[11px] text-slate-400">
                      {ev.sensor_readings.temperature !== undefined && (
                        <span>Temp: {formatTemp(ev.sensor_readings.temperature)}</span>
                      )}
                      {ev.sensor_readings.light !== undefined && (
                        <span>Light: {formatLux(ev.sensor_readings.light)}</span>
                      )}
                      {ev.sensor_readings.co2 !== undefined && (
                        <span>CO2: {formatCO2(ev.sensor_readings.co2)}</span>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-10 text-center text-xs">
          <History className="w-8 h-8 mx-auto text-slate-600 mb-2" />
          <h4 className="font-semibold text-slate-300">No Transition Events Emitted Yet</h4>
          <p className="text-slate-500 mt-1 max-w-sm mx-auto">
            Virtual fans and lights switch states only when temperature crosses hysteresis thresholds or when occupancy vacancy delays expire. Step or run the replay simulator to generate events.
          </p>
        </div>
      )}
    </div>
  );
}
