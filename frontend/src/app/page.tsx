"use client";

import React from "react";
import Link from "next/link";
import {
  Activity,
  ArrowRight,
  BarChart3,
  BrainCircuit,
  CheckCircle,
  Clock,
  Compass,
  Cpu,
  Database,
  History,
  Layers,
  PlaySquare,
  ShieldAlert,
  Sliders,
  Terminal,
} from "lucide-react";
import { ConnectionAlert } from "@/components/common/ConnectionAlert";

export default function HomePage() {
  return (
    <div className="space-y-12 max-w-6xl mx-auto py-2">
      <ConnectionAlert />

      {/* Hero Section */}
      <section className="relative rounded-2xl bg-gradient-to-b from-slate-900 to-slate-950 border border-slate-800 p-8 sm:p-12 overflow-hidden shadow-2xl">
        <div className="absolute top-0 right-0 w-96 h-96 bg-sky-500/10 rounded-full blur-3xl -mr-20 -mt-20 pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl -ml-20 -mb-20 pointer-events-none" />

        <div className="relative z-10 max-w-3xl space-y-5">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/20">
            <Cpu className="w-3.5 h-3.5" />
            <span>RoomIQ Intelligence Platform</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-slate-100 leading-tight">
            Intelligent Room Automation &{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-indigo-400">
              10-Minute Predictive Actuation
            </span>
          </h1>

          <p className="text-base sm:text-lg text-slate-400 leading-relaxed">
            RoomIQ pairs historical environmental time-series with machine learning to forecast room states 10 minutes ahead. A typed automation decision engine drives virtual fans and lighting using hysteresis bands and vacancy hold timers.
          </p>

          <div className="pt-3 flex flex-wrap items-center gap-3">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-sm transition-all shadow-lg shadow-sky-500/25"
            >
              <span>Launch Dashboard</span>
              <ArrowRight className="w-4 h-4" />
            </Link>

            <Link
              href="/simulation"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 font-semibold text-sm border border-slate-700 transition-colors"
            >
              <PlaySquare className="w-4 h-4 text-sky-400" />
              <span>Replay Simulator</span>
            </Link>

            <Link
              href="/architecture"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-slate-400 hover:text-slate-200 text-sm transition-colors"
            >
              <span>Architecture Pipeline</span>
            </Link>
          </div>
        </div>
      </section>

      {/* 4 Core Pillars */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-100">
              Platform Capabilities
            </h2>
            <p className="text-xs text-slate-400">
              Designed for deterministic evaluation, strict temporal hygiene, and verified ML actuation.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-colors">
            <div className="w-9 h-9 rounded-lg bg-sky-500/10 border border-sky-500/30 text-sky-400 flex items-center justify-center mb-3">
              <PlaySquare className="w-4 h-4" />
            </div>
            <h3 className="text-sm font-semibold text-slate-200 mb-1">
              Deterministic Replay
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Step sequentially through 9,752 benchmark sensor rows. Dynamic feature windowing physically prevents lookahead leakage.
            </p>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-colors">
            <div className="w-9 h-9 rounded-lg bg-purple-500/10 border border-purple-500/30 text-purple-400 flex items-center justify-center mb-3">
              <BrainCircuit className="w-4 h-4" />
            </div>
            <h3 className="text-sm font-semibold text-slate-200 mb-1">
              10-Minute Horizon
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Forecasts future occupancy (RandomForest, 94.8% test accuracy), future temperature (0.12°C MAE), and humidity at <code className="text-slate-300">t+10m</code>.
            </p>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-colors">
            <div className="w-9 h-9 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 flex items-center justify-center mb-3">
              <Sliders className="w-4 h-4" />
            </div>
            <h3 className="text-sm font-semibold text-slate-200 mb-1">
              Dual-Actuation Engine
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Virtual fan hysteresis prevents rapid toggling; 5-minute vacancy delay timers prevent lights turning off while room is occupied.
            </p>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-colors">
            <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center mb-3">
              <CheckCircle className="w-4 h-4" />
            </div>
            <h3 className="text-sm font-semibold text-slate-200 mb-1">
              Retrospective Auditing
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Holds predictions in memory and automatically compares them against sensor ground truth as time advances 10 minutes.
            </p>
          </div>
        </div>
      </section>

      {/* Module Navigation Grid */}
      <section className="space-y-4">
        <h2 className="text-lg font-bold text-slate-100">
          Explore RoomIQ Subsystems
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[
            {
              href: "/dashboard",
              title: "Room Overview",
              desc: "Real-time sensor telemetry, virtual actuators, and 10-minute forecast gauges.",
              icon: Activity,
              tag: "Main View",
            },
            {
              href: "/live-room",
              title: "Live Replay Snapshot",
              desc: "Current row inspection, physical thresholds, and retrospective evaluation.",
              icon: Compass,
              tag: "Inspection",
            },
            {
              href: "/analytics",
              title: "Sensor Analytics",
              desc: "Interactive Recharts time-series stream across temperature, humidity, and CO2.",
              icon: BarChart3,
              tag: "Telemetry",
            },
            {
              href: "/ai-insights",
              title: "AI Model Scorecard",
              desc: "Test split evaluation, confusion matrix, and feature importances.",
              icon: BrainCircuit,
              tag: "ML Metrics",
            },
            {
              href: "/control",
              title: "Control Policy Config",
              desc: "Configure fan hysteresis band, minimum switching delays, and light lux thresholds.",
              icon: Sliders,
              tag: "Automation",
            },
            {
              href: "/simulation",
              title: "Replay Simulator",
              desc: "Play, pause, single-step, and scrubber timeline for dataset sequences.",
              icon: PlaySquare,
              tag: "Simulator",
            },
            {
              href: "/events",
              title: "Transition Audit History",
              desc: "Full log of appliance state toggles with decision explanations and sensor snapshots.",
              icon: History,
              tag: "Audit Trail",
            },
            {
              href: "/reports",
              title: "Evaluation Reports",
              desc: "Phase 2A Data Quality report and Phase 2B Model Evaluation findings.",
              icon: Layers,
              tag: "Documentation",
            },
            {
              href: "/architecture",
              title: "System Architecture",
              desc: "5-layer ML pipeline diagrams and dynamic historical slicing mechanics.",
              icon: Database,
              tag: "System Design",
            },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className="group bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-sky-500/40 hover:bg-slate-900/90 transition-all shadow-sm"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="w-8 h-8 rounded-lg bg-slate-800 text-sky-400 group-hover:bg-sky-500/10 group-hover:text-sky-300 flex items-center justify-center transition-colors">
                    <Icon className="w-4 h-4" />
                  </div>
                  <span className="text-[10px] font-mono font-semibold uppercase text-slate-400 group-hover:text-sky-400 transition-colors">
                    {item.tag}
                  </span>
                </div>
                <h3 className="text-sm font-semibold text-slate-200 group-hover:text-slate-100 flex items-center gap-1.5">
                  <span>{item.title}</span>
                  <ArrowRight className="w-3.5 h-3.5 opacity-0 -translate-x-1 group-hover:opacity-100 group-hover:translate-x-0 transition-all text-sky-400" />
                </h3>
                <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                  {item.desc}
                </p>
              </Link>
            );
          })}
        </div>
      </section>
    </div>
  );
}
