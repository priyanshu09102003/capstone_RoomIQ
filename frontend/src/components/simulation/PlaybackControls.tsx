"use client";

import React from "react";
import { Play, Pause, RotateCcw, StepForward, Gauge } from "lucide-react";
import { SimulationStatus } from "@/types/api";

interface PlaybackControlsProps {
  status: SimulationStatus;
  playbackSpeed: number;
  loading?: boolean;
  onStart: () => void;
  onPause: () => void;
  onResume: () => void;
  onReset: () => void;
  onStep: () => void;
  onSpeedChange: (speed: number) => void;
}

export function PlaybackControls({
  status,
  playbackSpeed,
  loading = false,
  onStart,
  onPause,
  onResume,
  onReset,
  onStep,
  onSpeedChange,
}: PlaybackControlsProps) {
  const isRunning = status === "RUNNING";
  const isPaused = status === "PAUSED";
  const isCompleted = status === "COMPLETED";

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4 shadow-sm">
      <div className="flex items-center gap-2">
        {/* Play/Pause/Resume */}
        {!isRunning ? (
          <button
            onClick={isPaused ? onResume : onStart}
            disabled={loading || isCompleted}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold text-xs transition-colors disabled:opacity-50 shadow-sm shadow-sky-500/20"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            {isPaused ? "Resume Replay" : "Start Replay"}
          </button>
        ) : (
          <button
            onClick={onPause}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold text-xs transition-colors disabled:opacity-50"
          >
            <Pause className="w-3.5 h-3.5 fill-current" />
            Pause Replay
          </button>
        )}

        {/* Deterministic Step */}
        <button
          onClick={onStep}
          disabled={loading || isRunning || isCompleted}
          title={isRunning ? "Pause continuous playback to step manually" : "Advance exactly 1 minute"}
          className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors disabled:opacity-40"
        >
          <StepForward className="w-3.5 h-3.5 text-sky-400" />
          Single Step (1m)
        </button>

        {/* Reset */}
        <button
          onClick={onReset}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-800/80 hover:bg-slate-800 text-slate-400 hover:text-slate-200 text-xs font-medium border border-slate-700/80 transition-colors disabled:opacity-50"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Reset Replay
        </button>
      </div>

      {/* Speed Multiplier */}
      <div className="flex items-center gap-2 text-xs">
        <span className="text-slate-400 flex items-center gap-1 font-medium">
          <Gauge className="w-3.5 h-3.5 text-slate-400" />
          Speed:
        </span>
        <div className="inline-flex rounded-lg bg-slate-950 p-0.5 border border-slate-800">
          {[0.5, 1.0, 2.0, 5.0, 10.0].map((speed) => (
            <button
              key={speed}
              onClick={() => onSpeedChange(speed)}
              className={`px-2.5 py-1 rounded text-xs font-mono transition-colors ${
                playbackSpeed === speed
                  ? "bg-sky-500/20 text-sky-400 font-bold border border-sky-500/30"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {speed}x
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
