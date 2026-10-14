"use client";

import React from "react";
import { Fan, Lightbulb, Clock, Info } from "lucide-react";

interface ApplianceTileProps {
  device: "fan" | "light";
  state: boolean;
  reason?: string;
  lastSwitchedAt?: string | null;
  parameterNote?: string;
}

export function ApplianceTile({
  device,
  state,
  reason,
  lastSwitchedAt,
  parameterNote,
}: ApplianceTileProps) {
  const isFan = device === "fan";
  const label = isFan ? "Virtual Fan Actuator" : "Virtual Light Actuator";
  const icon = isFan ? (
    <Fan
      className={`w-5 h-5 ${state ? "text-cyan-400 animate-spin" : "text-slate-500"}`}
      style={{ animationDuration: state ? "3s" : "0s" }}
    />
  ) : (
    <Lightbulb
      className={`w-5 h-5 ${state ? "text-amber-400 fill-amber-400/20" : "text-slate-500"}`}
    />
  );

  const activeBadgeClasses = state
    ? isFan
      ? "bg-cyan-500/10 text-cyan-400 border-cyan-500/30"
      : "bg-amber-500/10 text-amber-400 border-amber-500/30"
    : "bg-slate-800 text-slate-400 border-slate-700/60";

  return (
    <div
      className={`bg-slate-900/90 border rounded-xl p-5 shadow-sm transition-all duration-200 ${
        state
          ? isFan
            ? "border-cyan-800/60 shadow-cyan-950/20"
            : "border-amber-800/60 shadow-amber-950/20"
          : "border-slate-800"
      }`}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <div
            className={`w-9 h-9 rounded-lg flex items-center justify-center border ${
              state
                ? isFan
                  ? "bg-cyan-950/70 border-cyan-800/60"
                  : "bg-amber-950/70 border-amber-800/60"
                : "bg-slate-800/60 border-slate-700/50"
            }`}
          >
            {icon}
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-100">{label}</h4>
            <span className="text-[10px] text-slate-400 uppercase tracking-wider">
              Software Model State
            </span>
          </div>
        </div>

        <span
          className={`px-3 py-1 rounded-full text-xs font-bold border tracking-wider ${activeBadgeClasses}`}
        >
          {state ? "ON" : "OFF"}
        </span>
      </div>

      <div className="mt-3 bg-slate-950/60 border border-slate-800/80 rounded-lg p-3 text-xs">
        <div className="flex items-start gap-1.5 text-slate-300">
          <Info className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            {reason || "Equilibrium state maintained. Ready for evaluation."}
          </p>
        </div>

        {(lastSwitchedAt || parameterNote) && (
          <div className="mt-2.5 pt-2 border-t border-slate-800/60 flex flex-wrap items-center justify-between gap-1 text-[11px] text-slate-400">
            {lastSwitchedAt && (
              <span className="flex items-center gap-1 font-mono">
                <Clock className="w-3 h-3 text-slate-500" />
                Toggle: {new Date(lastSwitchedAt).toLocaleTimeString()}
              </span>
            )}
            {parameterNote && (
              <span className="text-slate-400 italic">{parameterNote}</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
