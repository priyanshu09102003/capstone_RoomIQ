"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  BarChart3,
  BrainCircuit,
  Clock,
  Compass,
  FileText,
  History,
  Home,
  Info,
  Layers,
  PlaySquare,
  Sliders,
  X,
} from "lucide-react";

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

const navItems = [
  { href: "/", label: "Landing Overview", icon: Compass },
  { href: "/dashboard", label: "Dashboard", icon: Home },
  { href: "/live-room", label: "Live Room Snapshot", icon: Activity },
  { href: "/analytics", label: "Sensor Analytics", icon: BarChart3 },
  { href: "/ai-insights", label: "AI Insights & Models", icon: BrainCircuit },
  { href: "/control", label: "Policy Configuration", icon: Sliders },
  { href: "/simulation", label: "Replay Simulator", icon: PlaySquare },
  { href: "/events", label: "Transition History", icon: History },
  { href: "/reports", label: "Evaluation Reports", icon: FileText },
  { href: "/architecture", label: "System Architecture", icon: Layers },
  { href: "/about", label: "About & Limitations", icon: Info },
];

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const pathname = usePathname();

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm md:hidden"
        />
      )}

      {/* Sidebar drawer */}
      <aside
        className={`fixed md:sticky top-0 md:top-16 z-50 md:z-30 h-screen md:h-[calc(100vh-4rem)] w-64 bg-slate-950 border-r border-slate-800 transition-transform duration-300 ease-in-out shrink-0 overflow-y-auto ${
          isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        }`}
      >
        <div className="flex items-center justify-between p-4 md:hidden border-b border-slate-800">
          <span className="font-bold text-sm text-slate-200">Navigation</span>
          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-slate-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-3">
          <span className="px-3 text-[10px] font-semibold uppercase tracking-wider text-slate-400 block mb-2">
            Navigation Menu
          </span>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={onClose}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                    isActive
                      ? "bg-sky-500/15 text-sky-400 border border-sky-500/30 font-semibold"
                      : "text-slate-400 hover:text-slate-100 hover:bg-slate-900 border border-transparent"
                  }`}
                >
                  <Icon
                    className={`w-4 h-4 shrink-0 ${
                      isActive ? "text-sky-400" : "text-slate-400"
                    }`}
                  />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="p-4 mt-6 mx-3 rounded-xl bg-slate-900/60 border border-slate-800/80 text-xs text-slate-400">
          <div className="flex items-center gap-2 text-slate-300 font-semibold mb-1">
            <Clock className="w-3.5 h-3.5 text-sky-400" />
            <span>10-Minute Horizon</span>
          </div>
          <p className="text-[11px] leading-relaxed text-slate-400">
            Predictions target future states at <code className="text-slate-300">t+10m</code> without lookahead leakage.
          </p>
        </div>
      </aside>
    </>
  );
}
