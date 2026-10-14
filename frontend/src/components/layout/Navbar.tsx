"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Cpu, ExternalLink, Menu } from "lucide-react";
import { api, API_BASE_URL } from "@/lib/api";
import { HealthResponse } from "@/types/api";

interface NavbarProps {
  onToggleSidebar?: () => void;
}

export function Navbar({ onToggleSidebar }: NavbarProps) {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [offline, setOffline] = useState<boolean | null>(null);

  const checkHealth = async () => {
    try {
      const res = await api.getHealth();
      setHealth(res);
      setOffline(false);
    } catch {
      setHealth(null);
      setOffline(true);
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const isHealthy = health?.status === "healthy" && health.models_ready && health.data_ready;
  const isDegraded = health && !isHealthy;

  return (
    <header className="sticky top-0 z-40 w-full bg-slate-950/80 backdrop-blur-md border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={onToggleSidebar}
            className="md:hidden p-2 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 focus:outline-none"
            aria-label="Toggle menu"
          >
            <Menu className="w-5 h-5" />
          </button>

          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400 shadow-sm shadow-sky-500/20">
              <Cpu className="w-4 h-4" />
            </div>
            <div>
              <span className="font-bold text-base tracking-tight text-slate-100">
                Room<span className="text-sky-400">IQ</span>
              </span>
              <span className="hidden sm:inline-block ml-2 text-[10px] uppercase font-semibold text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded-full border border-slate-700/60">
                10-Min Predictive Actuator
              </span>
            </div>
          </Link>
        </div>

        <div className="flex items-center gap-3">
          {/* Health & Model Readiness Indicator */}
          <div
            className={`hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-mono border ${
              offline === null
                ? "bg-slate-900 text-slate-500 border-slate-800"
                : offline
                ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                : isDegraded
                ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                : "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
            }`}
            title={
              health
                ? `Models: ${health.models_ready ? "Ready" : "Not Loaded"}, Data: ${
                    health.data_ready ? "Ready" : "Missing"
                  }, Horizon: ${health.details?.horizon_minutes || 10}m`
                : "Backend is currently offline."
            }
          >
            <span
              className={`w-2 h-2 rounded-full ${
                offline === null
                  ? "bg-slate-500"
                  : offline
                  ? "bg-rose-500"
                  : isDegraded
                  ? "bg-amber-400"
                  : "bg-emerald-400 animate-pulse"
              }`}
            />
            <span>
              {offline === null
                ? "Checking API..."
                : offline
                ? "API Offline"
                : isDegraded
                ? "Degraded (Models Unready)"
                : "Models & Data Ready"}
            </span>
          </div>

          <a
            href={`${API_BASE_URL}/docs`}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200 px-2.5 py-1.5 rounded-lg hover:bg-slate-800/80 transition-colors"
          >
            <span>Swagger Docs</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>
    </header>
  );
}
