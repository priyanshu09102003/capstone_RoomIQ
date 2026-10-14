"use client";

import React from "react";
import { FileText, Database, ShieldCheck, AlertTriangle, CheckCircle2 } from "lucide-react";
import { ConnectionAlert } from "@/components/common/ConnectionAlert";

export default function ReportsPage() {
  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <ConnectionAlert />

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex items-center gap-2 mb-1">
          <FileText className="w-5 h-5 text-sky-400" />
          <h1 className="text-xl font-bold text-slate-100">
            RoomIQ Evaluation & Data Quality Reports
          </h1>
        </div>
        <p className="text-xs text-slate-400">
          Synthesized findings from Phase 2A (Data Inspection & Preprocessing) and Phase 2B (ML Training & Evaluation).
        </p>
      </div>

      {/* Phase 2A Data Quality Audit */}
      <section className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4 text-xs">
        <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
          <Database className="w-4 h-4 text-sky-400" />
          <h2 className="text-sm font-bold text-slate-100">
            Phase 2A: Data Quality & Discontinuity Audit
          </h2>
        </div>

        <p className="text-slate-300 leading-relaxed">
          The UCI Occupancy Detection dataset was inspected across all 3 raw partitions. Source files use comma delimiters, quoted timestamps in <code className="text-sky-300">YYYY-MM-DD HH:MM:SS</code> format, and a 1-minute nominal sampling interval.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 font-mono">
          <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
            <span className="text-[10px] text-slate-500 block">TRAINING PARTITION</span>
            <span className="text-sm font-bold text-slate-200">8,143 rows</span>
            <span className="text-[10px] text-slate-400 block mt-1">Feb 4 18:01 — Feb 10 09:33</span>
          </div>
          <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
            <span className="text-[10px] text-slate-500 block">TEST 1 PARTITION</span>
            <span className="text-sm font-bold text-slate-200">2,665 rows</span>
            <span className="text-[10px] text-slate-400 block mt-1">Feb 2 14:29 — Feb 4 10:43</span>
          </div>
          <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
            <span className="text-[10px] text-slate-500 block">TEST 2 PARTITION</span>
            <span className="text-sm font-bold text-slate-200">9,752 rows</span>
            <span className="text-[10px] text-slate-400 block mt-1">Feb 11 14:48 — Feb 18 09:19</span>
          </div>
        </div>

        <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3.5 space-y-2">
          <div className="flex items-center gap-1.5 font-semibold text-amber-300 text-xs">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>Temporal Boundary Discontinuities (Anti-Concatenation Finding)</span>
          </div>
          <p className="text-slate-400 text-[11px] leading-relaxed">
            Temporal analysis identified a <strong>7.4-hour gap</strong> between Test 1 and Training, and a <strong>29.2-hour gap</strong> between Training and Test 2. Merging these splits into a single contiguous array would create corrupted rolling windows and invalid lag computations. Each partition must be processed independently.
          </p>
        </div>
      </section>

      {/* Row Exclusion & Horizon Methodology */}
      <section className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4 text-xs">
        <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
          <ShieldCheck className="w-4 h-4 text-purple-400" />
          <h2 className="text-sm font-bold text-slate-100">
            Phase 2B: Strict Temporal Hygiene & Defensible Horizon
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-2">
            <h3 className="font-semibold text-slate-200 text-xs flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              Row Exclusion Rules (20 Rows / Split)
            </h3>
            <ul className="list-disc list-inside text-slate-400 space-y-1 text-[11px]">
              <li><strong>Head 10 rows dropped:</strong> Required to formulate legitimate 10-minute historical lags without artificial imputation.</li>
              <li><strong>Tail 10 rows dropped:</strong> Target matching requires a verified sensor reading at <code className="text-slate-300">t+10m</code>.</li>
              <li><strong>Zero NaNs:</strong> Exactly 20,500 clean, leak-free training and test samples remain.</li>
            </ul>
          </div>

          <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-2">
            <h3 className="font-semibold text-slate-200 text-xs flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-purple-400" />
              Why a 10-Minute Forecast Horizon?
            </h3>
            <p className="text-slate-400 text-[11px] leading-relaxed">
              A 10-minute predictive horizon aligns with commercial HVAC fan pre-cooling response times while maintaining high statistical predictability (94.8% occupancy accuracy; 0.12°C temperature MAE). Beyond 15 minutes, rapid outdoor weather shifts degrade accuracy.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
