// components/pedagogical/CriterionCard.tsx
// Detail card for a single criterion — shown on click or in a modal.

import type { CriterionResult } from "../../types/pedagogical";
import { severityToColor } from "../../utils/scoreUtils";

interface CriterionCardProps {
  criterion: CriterionResult;
  onClose?:  () => void;
}

export default function CriterionCard({ criterion, onClose }: CriterionCardProps) {
  const statusIcon  = criterion.passed ? "✅" : "❌";
  const severityBg  = {
    high:   "border-rose-200 bg-rose-50",
    medium: "border-amber-200 bg-amber-50",
    low:    "border-slate-200 bg-slate-50",
  }[criterion.severity];

  const scorePercent = criterion.weight > 0
    ? Math.round((criterion.score / criterion.weight) * 100) : 0;

  return (
    <div className="rounded-3xl border border-slate-200 bg-white shadow-lg overflow-hidden">

      {/* Header */}
      <div className="flex items-start justify-between gap-3 border-b border-slate-100 p-6">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
            Criterion Detail
          </p>
          <h3 className="mt-1 text-lg font-bold text-slate-900">{criterion.rule}</h3>
        </div>
        {onClose && (
          <button onClick={onClose}
            className="rounded-xl border border-slate-200 p-2 text-slate-400 hover:bg-slate-50">
            ✕
          </button>
        )}
      </div>

      <div className="p-6 space-y-5">

        {/* Status + Severity row */}
        <div className="flex flex-wrap gap-3">
          <span className={`inline-flex items-center gap-1.5 rounded-full px-4 py-1.5 text-sm font-semibold border ${severityBg}`}>
            {statusIcon} {criterion.passed ? "PASSED" : "FAILED"}
          </span>
          <span className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium ${severityToColor(criterion.severity)}`}>
            {criterion.severity.toUpperCase()} severity
          </span>
        </div>

        {/* Score gauge */}
        <div>
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="font-semibold text-slate-700">Score</span>
            <span className="font-bold text-slate-900">
              {criterion.score.toFixed(0)}/{criterion.weight.toFixed(0)}
              <span className="ml-2 text-xs font-normal text-slate-400">({scorePercent}%)</span>
            </span>
          </div>
          <div className="h-3 w-full overflow-hidden rounded-full bg-slate-100">
            <div
              className={`h-full rounded-full transition-all duration-700 ${criterion.passed ? "bg-emerald-500" : "bg-rose-400"}`}
              style={{ width: `${scorePercent}%` }}
            />
          </div>
        </div>

        {/* Finding */}
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400 mb-2">Finding</p>
          <p className="text-sm text-slate-700 leading-relaxed">
            {criterion.message || "—"}
          </p>
        </div>

        {/* Recommendation */}
        {criterion.recommendation && (
          <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4">
            <p className="text-xs font-semibold text-amber-700 mb-1">💡 Recommendation</p>
            <p className="text-sm text-amber-900">{criterion.recommendation}</p>
          </div>
        )}

        {/* ISO reference */}
        {criterion.iso_reference && (
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400 mb-2">Standard</p>
            <span className="rounded-full border border-violet-200 bg-violet-50 px-3 py-0.5 text-xs text-violet-700">
              {criterion.iso_reference}
            </span>
          </div>
        )}

        {/* Technical details */}
        {criterion.details && Object.keys(criterion.details).length > 0 && (
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400 mb-2">Details</p>
            <pre className="overflow-auto rounded-2xl bg-slate-950 p-4 text-xs text-emerald-300 max-h-48">
              {JSON.stringify(criterion.details, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}