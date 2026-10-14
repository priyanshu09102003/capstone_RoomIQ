"use client";

import React from "react";
import { Check, X, ShieldAlert, Award } from "lucide-react";

interface ConfusionMatrixProps {
  tn?: number;
  fp?: number;
  fn?: number;
  tp?: number;
  accuracy?: number;
  precision?: number;
  recall?: number;
  f1?: number;
  rocAuc?: number | null;
  splitName?: string;
}

export function ConfusionMatrixCard({
  tn = 7668,
  fp = 35,
  fn = 468,
  tp = 1561,
  accuracy = 0.9483,
  precision = 0.9781,
  recall = 0.7693,
  f1 = 0.8612,
  rocAuc = 0.9622,
  splitName = "Test 2 Partition (9,732 samples)",
}: ConfusionMatrixProps) {
  const total = tn + fp + fn + tp;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm text-xs">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-100">
            Occupancy Classification Confusion Matrix
          </h3>
          <span className="text-[10px] text-slate-400 font-mono">
            EVALUATED ON {splitName.toUpperCase()}
          </span>
        </div>
        <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          {(accuracy * 100).toFixed(1)}% Accuracy
        </span>
      </div>

      {/* 2x2 Matrix Grid */}
      <div className="grid grid-cols-2 gap-2.5 mb-4 font-mono">
        {/* True Negative */}
        <div className="bg-slate-950/80 border border-emerald-900/40 rounded-lg p-3">
          <div className="flex justify-between text-slate-400 text-[10px] mb-1">
            <span>TRUE NEGATIVE</span>
            <span className="text-emerald-400 font-bold">TN</span>
          </div>
          <div className="text-lg font-bold text-slate-100">{tn.toLocaleString()}</div>
          <div className="text-[10px] text-slate-500">
            Correctly Vacant ({((tn / total) * 100).toFixed(1)}%)
          </div>
        </div>

        {/* False Positive */}
        <div className="bg-slate-950/80 border border-amber-900/40 rounded-lg p-3">
          <div className="flex justify-between text-slate-400 text-[10px] mb-1">
            <span>FALSE POSITIVE</span>
            <span className="text-amber-400 font-bold">FP</span>
          </div>
          <div className="text-lg font-bold text-slate-100">{fp.toLocaleString()}</div>
          <div className="text-[10px] text-slate-500">
            False Alarm ({((fp / total) * 100).toFixed(1)}%)
          </div>
        </div>

        {/* False Negative */}
        <div className="bg-slate-950/80 border border-rose-900/40 rounded-lg p-3">
          <div className="flex justify-between text-slate-400 text-[10px] mb-1">
            <span>FALSE NEGATIVE</span>
            <span className="text-rose-400 font-bold">FN</span>
          </div>
          <div className="text-lg font-bold text-slate-100">{fn.toLocaleString()}</div>
          <div className="text-[10px] text-slate-500">
            Missed Detection ({((fn / total) * 100).toFixed(1)}%)
          </div>
        </div>

        {/* True Positive */}
        <div className="bg-slate-950/80 border border-emerald-900/40 rounded-lg p-3">
          <div className="flex justify-between text-slate-400 text-[10px] mb-1">
            <span>TRUE POSITIVE</span>
            <span className="text-emerald-400 font-bold">TP</span>
          </div>
          <div className="text-lg font-bold text-slate-100">{tp.toLocaleString()}</div>
          <div className="text-[10px] text-slate-500">
            Correctly Occupied ({((tp / total) * 100).toFixed(1)}%)
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-4 gap-2 pt-3 border-t border-slate-800 text-center font-mono">
        <div>
          <span className="text-[10px] text-slate-400 block">PRECISION</span>
          <span className="text-xs font-bold text-slate-200">{(precision * 100).toFixed(1)}%</span>
        </div>
        <div>
          <span className="text-[10px] text-slate-400 block">RECALL</span>
          <span className="text-xs font-bold text-slate-200">{(recall * 100).toFixed(1)}%</span>
        </div>
        <div>
          <span className="text-[10px] text-slate-400 block">F1 SCORE</span>
          <span className="text-xs font-bold text-slate-200">{(f1 * 100).toFixed(1)}%</span>
        </div>
        <div>
          <span className="text-[10px] text-slate-400 block">ROC-AUC</span>
          <span className="text-xs font-bold text-purple-400">
            {rocAuc ? rocAuc.toFixed(3) : "N/A"}
          </span>
        </div>
      </div>
    </div>
  );
}
