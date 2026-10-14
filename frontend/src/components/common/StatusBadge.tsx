import React from "react";

interface StatusBadgeProps {
  status: string;
  size?: "sm" | "md";
}

export function StatusBadge({ status, size = "md" }: StatusBadgeProps) {
  const norm = status.toUpperCase();

  let colorClasses = "bg-slate-800 text-slate-300 border-slate-700";
  let dotColor = "bg-slate-400";

  if (norm === "RUNNING" || norm === "ONLINE" || norm === "HEALTHY") {
    colorClasses = "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
    dotColor = "bg-emerald-400";
  } else if (norm === "PAUSED" || norm === "DEGRADED") {
    colorClasses = "bg-amber-500/10 text-amber-400 border-amber-500/20";
    dotColor = "bg-amber-400";
  } else if (norm === "COMPLETED") {
    colorClasses = "bg-purple-500/10 text-purple-400 border-purple-500/20";
    dotColor = "bg-purple-400";
  } else if (norm === "IDLE" || norm === "OFFLINE") {
    colorClasses = "bg-slate-800/80 text-slate-400 border-slate-700/60";
    dotColor = "bg-slate-400";
  }

  const padding = size === "sm" ? "px-2 py-0.5 text-[10px]" : "px-2.5 py-1 text-xs";

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-medium rounded-full border ${padding} ${colorClasses}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${dotColor} ${norm === "RUNNING" ? "animate-pulse" : ""}`} />
      {norm}
    </span>
  );
}
