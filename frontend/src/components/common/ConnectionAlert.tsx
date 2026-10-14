"use client";

import React, { useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, RefreshCw, Terminal } from "lucide-react";
import { api } from "@/lib/api";

export function ConnectionAlert() {
  const [isOnline, setIsOnline] = useState<boolean | null>(null);
  const [checking, setChecking] = useState(false);

  const checkStatus = async () => {
    setChecking(true);
    const reachable = await api.isReachable();
    setIsOnline(reachable);
    setChecking(false);
  };

  useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  if (isOnline === null) {
    return null;
  }

  if (isOnline) {
    return null; // Don't clutter UI when connected
  }

  return (
    <div className="bg-amber-950/40 border border-amber-800/60 rounded-xl p-4 mb-6 shadow-lg shadow-amber-950/20">
      <div className="flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
        <div className="flex-1 text-sm">
          <div className="flex items-center justify-between">
            <h4 className="font-semibold text-amber-200">
              Backend Service Not Detected (Port 8000)
            </h4>
            <button
              onClick={checkStatus}
              disabled={checking}
              className="inline-flex items-center gap-1 text-xs text-amber-300 hover:text-amber-100 bg-amber-900/40 hover:bg-amber-900/60 px-2.5 py-1 rounded border border-amber-700/50 transition-colors"
            >
              <RefreshCw className={`w-3 h-3 ${checking ? "animate-spin" : ""}`} />
              Retry Connection
            </button>
          </div>
          <p className="text-amber-300/80 mt-1 text-xs leading-relaxed">
            The frontend is operating in <strong>disconnected inspection mode</strong>. To execute real-time model inference, chronological stepping, or policy adjustments, launch the FastAPI server:
          </p>
          <div className="mt-2.5 flex items-center gap-2 bg-slate-950/80 border border-slate-800 rounded-lg p-2 font-mono text-xs text-slate-300 overflow-x-auto">
            <Terminal className="w-3.5 h-3.5 text-sky-400 shrink-0" />
            <code>.\\ml\\.venv\\Scripts\\python ml/run_api.py --reload</code>
          </div>
        </div>
      </div>
    </div>
  );
}
