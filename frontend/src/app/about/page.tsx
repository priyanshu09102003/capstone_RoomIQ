"use client";

import React from "react";
import { Info, BookOpen, AlertTriangle, Cpu, Layers } from "lucide-react";
import { ConnectionAlert } from "@/components/common/ConnectionAlert";

export default function AboutPage() {
  return (
    <div className="space-y-8 max-w-4xl mx-auto text-xs">
      <ConnectionAlert />

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex items-center gap-2 mb-1">
          <Info className="w-5 h-5 text-sky-400" />
          <h1 className="text-xl font-bold text-slate-100">
            About RoomIQ, Dataset Attribution & Scope
          </h1>
        </div>
        <p className="text-slate-400 text-xs">
          Comprehensive project background, academic benchmark citation, stack details, and system boundaries.
        </p>
      </div>

      {/* Dataset Citation */}
      <section className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-3">
        <div className="flex items-center gap-2 pb-2 border-b border-slate-800">
          <BookOpen className="w-4 h-4 text-sky-400" />
          <h2 className="text-sm font-bold text-slate-100">
            Benchmark Dataset Attribution
          </h2>
        </div>

        <p className="text-slate-300 leading-relaxed">
          The RoomIQ project is built and benchmarked upon the canonical <strong>Occupancy Detection Data Set</strong> from the UCI Machine Learning Repository.
        </p>

        <blockquote className="bg-slate-950 p-4 rounded-lg border-l-2 border-sky-400 text-slate-400 font-mono text-[11px] leading-relaxed">
          Candanedo, L. M., & Feldheim, V. (2016). Accurate occupancy detection of an office room from light, temperature, humidity and CO2 measurements using statistical learning models. <em>Energy and Buildings</em>, 112, 28-39.
        </blockquote>

        <p className="text-slate-400 text-[11px]">
          The dataset provides 20,560 1-minute digital sensor observations collected across an experimental room in Mons, Belgium, capturing temperature, relative humidity, light (Lux), CO2 (ppm), humidity ratio, and ground truth binary occupancy determined via digital photography.
        </p>
      </section>

      {/* Technology Stack */}
      <section className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <div className="flex items-center gap-2 pb-2 border-b border-slate-800">
          <Layers className="w-4 h-4 text-purple-400" />
          <h2 className="text-sm font-bold text-slate-100">
            Technology Stack
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-mono">
          <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-1">
            <span className="font-bold text-sky-400 text-xs block">Frontend Layer</span>
            <div className="text-slate-300 text-[11px]">Next.js 16.4 App Router (Turbopack)</div>
            <div className="text-slate-400 text-[11px]">React 19 & TypeScript 5</div>
            <div className="text-slate-400 text-[11px]">Tailwind CSS 4</div>
            <div className="text-slate-400 text-[11px]">Recharts 2.15 & Lucide React 1.56</div>
          </div>

          <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-1">
            <span className="font-bold text-emerald-400 text-xs block">Backend & ML Core</span>
            <div className="text-slate-300 text-[11px]">FastAPI 0.143 & Uvicorn 0.54</div>
            <div className="text-slate-400 text-[11px]">scikit-learn 1.9 & joblib 1.6</div>
            <div className="text-slate-400 text-[11px]">pandas 3.0 & numpy 2.5</div>
            <div className="text-slate-400 text-[11px]">Pydantic 2.14 & pytest 9.1</div>
          </div>
        </div>
      </section>

      {/* Project Limitations */}
      <section className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-3">
        <div className="flex items-center gap-2 pb-2 border-b border-slate-800 text-amber-300">
          <AlertTriangle className="w-4 h-4 text-amber-400" />
          <h2 className="text-sm font-bold">
            Transparent Project Scope & Limitations
          </h2>
        </div>

        <ul className="space-y-2 text-slate-400 text-[11px] leading-relaxed">
          <li className="flex items-start gap-2">
            <span className="text-amber-400 font-bold">1.</span>
            <span>
              <strong>Virtual Software Actuators:</strong> Appliances (virtual fan and light) are modeled software states within the decision engine. The project does not interface with physical MQTT, Zigbee, or GPIO relay hardware.
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-amber-400 font-bold">2.</span>
            <span>
              <strong>Demonstration Heuristics:</strong> Thresholds (21.5°C / 22.5°C for fan; 250 Lux for lights) are demonstration defaults and have not been scientifically optimized for specific building codes or ASHRAE 55 thermal comfort standards.
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-amber-400 font-bold">3.</span>
            <span>
              <strong>Deterministic Replay Environment:</strong> Sensor streams are deterministic replays of historical benchmark records. The system does not claim to operate on physical live sensor feeds.
            </span>
          </li>
        </ul>
      </section>
    </div>
  );
}
