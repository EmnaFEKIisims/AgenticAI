// components/planning/ImpactPanel.tsx
// Full impact analysis modal shown after admin drops a session.

import { useState } from "react";
import type { ImpactResponse }  from "../../types/impactAnalysis";
import type { PendingMove }     from "../../types/scheduleMove";
import ImpactSummary from "./ImpactSummary";

interface ImpactPanelProps {
  pendingMove: PendingMove;
  impact:      ImpactResponse;
  isApplying:  boolean;
  onConfirm:   (adminNote?: string) => void;
  onCancel:    () => void;
}

export default function ImpactPanel({
  pendingMove, impact, isApplying, onConfirm, onCancel,
}: ImpactPanelProps) {

  const [note, setNote] = useState("");

  const { target } = pendingMove;
  const targetLabel = `${target.day} ${target.time_slot.split("→")[0].trim()} (Week ${target.week})`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
      <div className="w-full max-w-md rounded-3xl border border-slate-200 bg-white shadow-2xl overflow-hidden">

        {/* Header */}
        <div className="border-b border-slate-100 px-6 py-5">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Impact Analysis
          </p>
          <h3 className="mt-1 text-base font-bold text-slate-900">
            Move «{pendingMove.course_title}»
          </h3>
          <p className="text-sm text-slate-600 mt-0.5">
            → <strong>{targetLabel}</strong>
          </p>
        </div>

        {/* Impact summary */}
        <div className="px-6 py-5 space-y-4">
          {/* Global verdict */}
          <div className={`rounded-2xl border p-3 ${impact.is_safe ? "border-emerald-200 bg-emerald-50" : "border-amber-200 bg-amber-50"}`}>
            <p className={`text-sm font-semibold ${impact.is_safe ? "text-emerald-800" : "text-amber-800"}`}>
              {impact.is_safe ? "✅ No conflicts — safe to move" : `⚠️ ${impact.new_conflicts.length} conflict(s) detected`}
            </p>
            <p className="text-xs text-slate-600 mt-0.5">{impact.recommendation}</p>
          </div>

          <ImpactSummary impact={impact} />

          {/* Admin note */}
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Note (optional)
            </label>
            <input
              type="text"
              value={note}
              onChange={e => setNote(e.target.value)}
              placeholder="Reason for this move..."
              className="mt-1.5 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800 outline-none focus:border-slate-400"
            />
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3 border-t border-slate-100 px-6 py-4">
          <button
            onClick={() => onConfirm(note || undefined)}
            disabled={isApplying}
            className={`flex-1 rounded-xl py-2.5 text-sm font-semibold text-white transition disabled:opacity-60 ${
              impact.is_safe ? "bg-emerald-600 hover:bg-emerald-700" : "bg-amber-600 hover:bg-amber-700"
            }`}
          >
            {isApplying
              ? <span className="flex items-center justify-center gap-2"><span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" /> Moving…</span>
              : impact.is_safe ? "✅ Confirm move" : "⚠️ Move anyway"
            }
          </button>
          <button onClick={onCancel} disabled={isApplying}
            className="flex-1 rounded-xl border border-slate-200 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition">
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}