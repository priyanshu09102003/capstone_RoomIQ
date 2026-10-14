"use client";

import React from "react";
import { AlertCircle, Cpu } from "lucide-react";

export function SystemBanner() {
  return (
    <div className="w-full bg-slate-900/90 border-b border-sky-900/40 px-4 py-2 text-xs text-slate-300">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/20">
            <Cpu className="w-3 h-3" />
            DATASET REPLAY / SIMULATION
          </span>
          <span className="text-slate-400 hidden sm:inline">
            Deterministic evaluation engine replaying UCI Occupancy Detection time-series.
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-slate-400">
          <AlertCircle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
          <span>Virtual software actuators — not physical hardware.</span>
        </div>
      </div>
    </div>
  );
}
