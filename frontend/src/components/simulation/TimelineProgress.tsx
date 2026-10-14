"use client";

import React from "react";
import { Clock, Database } from "lucide-react";
import { StatusBadge } from "@/components/common/StatusBadge";
import { SimulationStatus } from "@/types/api";

interface TimelineProgressProps {
  currentIndex: number;
  totalRecords: number;
  currentTimestamp?: string | null;
  status: SimulationStatus;
  splitName?: string;
}

export function TimelineProgress({
  currentIndex,
  totalRecords,
  currentTimestamp,
  status,
  splitName = "test2",
}: TimelineProgressProps) {
  const percent = totalRecords > 0 ? Math.min(100, Math.round((currentIndex / totalRecords) * 100)) : 0;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm text-xs">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-2.5">
        <div className="flex items-center gap-3">
          <StatusBadge status={status} />
          <span className="text-slate-300 font-semibold flex items-center gap-1.5 font-mono">
            <Database className="w-3.5 h-3.5 text-sky-400" />
            {splitName}_clean.csv
          </span>
          <span className="text-slate-400 font-mono">
            Record: {currentIndex.toLocaleString()} / {totalRecords.toLocaleString()} ({percent}%)
          </span>
        </div>

        {currentTimestamp && (
          <div className="flex items-center gap-1.5 font-mono text-slate-300 bg-slate-950 px-2.5 py-1 rounded border border-slate-800">
            <Clock className="w-3.5 h-3.5 text-sky-400" />
            <span>{new Date(currentTimestamp).toLocaleString()}</span>
          </div>
        )}
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
        <div
          className="bg-gradient-to-r from-sky-500 to-indigo-500 h-2 rounded-full transition-all duration-300"
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}
