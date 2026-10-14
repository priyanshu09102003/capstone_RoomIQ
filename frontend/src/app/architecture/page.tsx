"use client";

import React from "react";
import { Layers, Database, Cpu, Sliders, PlaySquare, Globe, ShieldCheck } from "lucide-react";
import { ConnectionAlert } from "@/components/common/ConnectionAlert";

export default function ArchitecturePage() {
  const pipelineLayers = [
    {
      num: "01",
      title: "Data Preprocessing & Validation",
      module: "ml/src/data/",
      desc: "Cleans UCI Occupancy Detection records, parses quoted ISO timestamps, discards leakage-prone row IDs, and handles temporal inter-split discontinuities independently.",
      icon: Database,
      tag: "Data Pipeline",
    },
    {
      num: "02",
      title: "Zero-Leakage Feature Engineering",
      module: "ml/src/features/",
      desc: "Engineers 50 non-leaking features using only past records (≤ t_k). Computes 1m/5m/10m lags, 5m/10m diffs, 5m/15m rolling means, and cyclical sin/cos time encodings.",
      icon: Cpu,
      tag: "Feature Store",
    },
    {
      num: "03",
      title: "10-Minute Machine Learning Predictors",
      module: "ml/src/models/",
      desc: "Production inference engine loading saved joblib artifacts: RandomForest for binary occupancy, GradientBoosting for temperature trajectory, and Ridge for humidity.",
      icon: ShieldCheck,
      tag: "ML Models",
    },
    {
      num: "04",
      title: "Automation Control Engine",
      module: "ml/src/control/",
      desc: "Deterministic decision engine actuating virtual fans (hysteresis band 21.5-22.5°C, 300s switching lock) and virtual lights (lux < 250, 300s vacancy hold timer).",
      icon: Sliders,
      tag: "Control Policy",
    },
    {
      num: "05",
      title: "Deterministic Dataset Replay Simulator",
      module: "ml/src/simulation/",
      desc: "State machine managing chronological replay, dynamic historical slicing (max 0, k-25 : k+1), actuation, and automatic retrospective forecast evaluation.",
      icon: PlaySquare,
      tag: "Simulation Core",
    },
    {
      num: "06",
      title: "FastAPI REST & Streaming Service",
      module: "ml/src/api/",
      desc: "High-performance Python backend with thread-safe asyncio locking, CORS whitelisting for Next.js, sanitized error masking, and health readiness separation.",
      icon: Globe,
      tag: "REST API",
    },
  ];

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <ConnectionAlert />

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex items-center gap-2 mb-1">
          <Layers className="w-5 h-5 text-sky-400" />
          <h1 className="text-xl font-bold text-slate-100">
            RoomIQ System Architecture & ML Workflow
          </h1>
        </div>
        <p className="text-xs text-slate-400">
          Modular 6-layer design ensuring strict temporal hygiene, thread-safe replay, and verifiable actuation.
        </p>
      </div>

      {/* Pipeline Layers Grid */}
      <div className="space-y-3">
        {pipelineLayers.map((layer) => {
          const Icon = layer.icon;
          return (
            <div
              key={layer.num}
              className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:border-slate-700 transition-colors"
            >
              <div className="flex items-start gap-4">
                <span className="font-mono text-xl font-extrabold text-slate-600 shrink-0">
                  {layer.num}
                </span>
                <div className="w-9 h-9 rounded-lg bg-sky-500/10 border border-sky-500/30 text-sky-400 flex items-center justify-center shrink-0">
                  <Icon className="w-4 h-4" />
                </div>
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="font-semibold text-sm text-slate-100">
                      {layer.title}
                    </h3>
                    <code className="text-[10px] bg-slate-950 px-2 py-0.5 rounded border border-slate-800 text-sky-400 font-mono">
                      {layer.module}
                    </code>
                  </div>
                  <p className="text-xs text-slate-400 mt-1 leading-relaxed max-w-2xl">
                    {layer.desc}
                  </p>
                </div>
              </div>

              <span className="text-[10px] font-mono font-bold uppercase text-slate-400 px-2.5 py-1 rounded bg-slate-950 border border-slate-800 self-start sm:self-center shrink-0">
                {layer.tag}
              </span>
            </div>
          );
        })}
      </div>

      {/* Dynamic Historical Windowing Deep Dive */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-xs space-y-3">
        <h3 className="text-sm font-semibold text-slate-100">
          Dynamic Historical Windowing Mechanics
        </h3>
        <p className="text-slate-400 leading-relaxed">
          In typical offline ML setups, naive dataset shifts inadvertently leak future sensor rows into rolling statistics. RoomIQ completely eliminates this vulnerability during live replay:
        </p>

        <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 font-mono text-slate-300 space-y-2 text-[11px] overflow-x-auto">
          <div className="text-slate-400"># At chronological replay step k:</div>
          <div>window_start = max(0, k - 25)</div>
          <div>window_df = raw_dataset.iloc[window_start : k + 1]  <span className="text-emerald-400"># Strictly &le; k</span></div>
          <div>features = build_features(window_df).iloc[-1]      <span className="text-sky-400"># Exact terminal row</span></div>
        </div>

        <p className="text-slate-400 leading-relaxed text-[11px]">
          Because <code className="text-slate-200">raw_dataset.iloc[k + 1 :]</code> is never loaded into memory during step <code className="text-slate-200">k</code>, it is mathematically impossible for future sensor readings or future targets to contaminate model predictions.
        </p>
      </div>
    </div>
  );
}
