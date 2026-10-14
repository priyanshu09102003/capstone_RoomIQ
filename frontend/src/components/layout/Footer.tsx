import React from "react";

export function Footer() {
  return (
    <footer className="w-full bg-slate-950 border-t border-slate-800/80 py-6 px-4 text-xs text-slate-500 mt-auto">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex flex-col gap-1 text-center sm:text-left">
          <p className="text-slate-400">
            <strong>RoomIQ</strong> — Intelligent Room Automation & 10-Minute Predictive Actuation.
          </p>
          <p className="text-[11px] text-slate-500">
            Benchmark Dataset: UCI Occupancy Detection Data Set (Candanedo & Feldheim, 2016).
          </p>
        </div>
        <div className="flex items-center gap-4 text-slate-400">
          <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-900 border border-slate-800 text-slate-400">
            SYSTEM CLASSIFICATION: REPLAY / SIMULATION
          </span>
        </div>
      </div>
    </footer>
  );
}
