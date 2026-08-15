// components/planning/ImpactSummary.tsx
// Compact inline summary of an impact analysis (used inside ImpactPanel).

import type { ImpactResponse } from "../../types/impactAnalysis";

interface ImpactSummaryProps {
  impact: ImpactResponse;
}

export default function ImpactSummary({ impact }: ImpactSummaryProps) {
  const { new_conflicts, resolved_conflicts, affected_sessions, is_safe } = impact;

  return (
    <div className="space-y-3">

      {/* Quick counts */}
      <div className="grid grid-cols-3 gap-2">
        <div className={`rounded-xl border p-3 text-center ${is_safe ? "border-emerald-200 bg-emerald-50" : "border-rose-200 bg-rose-50"}`}>
          <p className={`text-2xl font-bold ${is_safe ? "text-emerald-600" : "text-rose-600"}`}>
            {new_conflicts.length}
          </p>
          <p className="text-xs text-slate-600 mt-0.5">New conflicts</p>
        </div>
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-center">
          <p className="text-2xl font-bold text-emerald-600">{resolved_conflicts.length}</p>
          <p className="text-xs text-slate-600 mt-0.5">Resolved</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-center">
          <p className="text-2xl font-bold text-slate-600">{affected_sessions.length}</p>
          <p className="text-xs text-slate-600 mt-0.5">Affected</p>
        </div>
      </div>

      {/* New conflicts list */}
      {new_conflicts.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-xs font-semibold uppercase tracking-wider text-rose-700">New conflicts</p>
          {new_conflicts.map((c, i) => (
            <div key={i} className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-800">
              {c.description}
            </div>
          ))}
        </div>
      )}

      {/* Resolved conflicts */}
      {resolved_conflicts.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-xs font-semibold uppercase tracking-wider text-emerald-700">Conflicts resolved</p>
          {resolved_conflicts.map((c, i) => (
            <div key={i} className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-800">
              ✅ {c.description}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}