"use client";

import React, { ReactNode } from "react";

interface MetricCardProps {
  title: string;
  value?: number | string | null;
  unit?: string;
  icon: ReactNode;
  subtitle?: string;
  badge?: string;
  accentColor?: "cyan" | "emerald" | "amber" | "purple";
}

export function MetricCard({
  title,
  value,
  unit,
  icon,
  subtitle,
  badge,
  accentColor = "cyan",
}: MetricCardProps) {
  const borderColors = {
    cyan: "border-sky-800/40 hover:border-sky-500/40",
    emerald: "border-emerald-800/40 hover:border-emerald-500/40",
    amber: "border-amber-800/40 hover:border-amber-500/40",
    purple: "border-purple-800/40 hover:border-purple-500/40",
  };

  const iconColors = {
    cyan: "text-sky-400 bg-sky-950/60 border-sky-800/50",
    emerald: "text-emerald-400 bg-emerald-950/60 border-emerald-800/50",
    amber: "text-amber-400 bg-amber-950/60 border-amber-800/50",
    purple: "text-purple-400 bg-purple-950/60 border-purple-800/50",
  };

  const formattedValue =
    value !== undefined && value !== null
      ? typeof value === "number"
        ? value.toLocaleString(undefined, { maximumFractionDigits: 2 })
        : value
      : null;

  return (
    <div
      className={`bg-slate-900/90 border rounded-xl p-5 shadow-sm transition-all duration-200 ${borderColors[accentColor]}`}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium text-slate-400 tracking-wide uppercase">
          {title}
        </span>
        <div
          className={`w-8 h-8 rounded-lg flex items-center justify-center border ${iconColors[accentColor]}`}
        >
          {icon}
        </div>
      </div>

      <div className="flex items-baseline gap-1.5">
        {formattedValue !== null ? (
          <>
            <span className="text-2xl font-bold tracking-tight text-slate-100 font-mono">
              {formattedValue}
            </span>
            {unit && (
              <span className="text-sm font-medium text-slate-400">{unit}</span>
            )}
          </>
        ) : (
          <span className="text-sm text-slate-500 italic">No data yet</span>
        )}
      </div>

      {(subtitle || badge) && (
        <div className="mt-3 pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
          <span>{subtitle}</span>
          {badge && (
            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-800 text-slate-300 border border-slate-700/60">
              {badge}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
