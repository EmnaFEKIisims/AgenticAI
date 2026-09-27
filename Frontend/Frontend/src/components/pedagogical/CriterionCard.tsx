// components/pedagogical/CriterionCard.tsx
// Detail card for a single criterion — shown on click or in a modal.

import { CheckCircle2, XCircle, X, Lightbulb, ShieldCheck, FileText } from "lucide-react";
import type { CriterionResult } from "../../types/pedagogical";
import { severityToColor } from "../../utils/scoreUtils";

interface CriterionCardProps {
  criterion: CriterionResult;
  onClose?:  () => void;
}

export default function CriterionCard({ criterion, onClose }: CriterionCardProps) {
  const StatusIcon = criterion.passed ? CheckCircle2 : XCircle;
  const severityBg = {
    high:   "border-rose-100 bg-rose-50 text-rose-700",
    medium: "border-amber-100 bg-amber-50 text-amber-700",
    low:    "border-slate-200 bg-slate-50 text-slate-700",
  }[criterion.severity];

  const scorePercent = criterion.weight > 0
    ? Math.round((criterion.score / criterion.weight) * 100) : 0;

  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-lg">
      {/* Header */}
      <header className="flex items-start justify-between gap-3 border-b border-slate-100 bg-linear-to-br from-slate-50 via-white to-white px-6 py-5">
        <div className="flex items-start gap-4">
          <span
            className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border shadow-sm ${
              criterion.passed
                ? "border-emerald-100 bg-emerald-50 text-emerald-600"
                : "border-rose-100 bg-rose-50 text-rose-600"
            }`}
          >
            <StatusIcon className="h-5 w-5" aria-hidden="true" />
          </span>
          <div className="min-w-0">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Criterion detail
            </p>
            <h3 className="mt-0.5 text-base font-semibold tracking-tight text-slate-900">
              {criterion.rule}
            </h3>
          </div>
        </div>

        {onClose && (
          <button
            onClick={onClose}
            className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        )}
      </header>

      <div className="space-y-5 bg-slate-50/40 p-6">
        {/* Status + severity */}
        <div className="flex flex-wrap gap-2">
          <span
            className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold ${severityBg}`}
          >
            <StatusIcon className="h-3.5 w-3.5" aria-hidden="true" />
            {criterion.passed ? "Passed" : "Failed"}
          </span>
          <span
            className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium ${severityToColor(criterion.severity)}`}
          >
            {criterion.severity.toUpperCase()} severity
          </span>
        </div>

        {/* Score */}
        <div className="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
          <div className="mb-2 flex items-center justify-between text-sm">
            <span className="font-medium text-slate-600">Score</span>
            <span className="font-mono font-semibold text-slate-900">
              {criterion.score.toFixed(0)}
              <span className="text-slate-400">/{criterion.weight.toFixed(0)}</span>
              <span className="ml-2 text-xs font-normal text-slate-400">({scorePercent}%)</span>
            </span>
          </div>
          <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
            <div
              className={`h-full rounded-full transition-all duration-700 ${
                criterion.passed ? "bg-emerald-500" : "bg-rose-400"
              }`}
              style={{ width: `${scorePercent}%` }}
            />
          </div>
        </div>

        {/* Finding */}
        <div className="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
          <p className="mb-2 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            <FileText className="h-3 w-3" aria-hidden="true" />
            Finding
          </p>
          <p className="text-sm leading-relaxed text-slate-700">
            {criterion.message || "—"}
          </p>
        </div>

        {/* Recommendation */}
        {criterion.recommendation && (
          <div className="rounded-2xl border border-amber-100 bg-amber-50/60 p-4 shadow-sm">
            <p className="mb-1.5 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-amber-700">
              <Lightbulb className="h-3.5 w-3.5" aria-hidden="true" />
              Recommendation
            </p>
            <p className="text-sm leading-relaxed text-amber-900">
              {criterion.recommendation}
            </p>
          </div>
        )}

        {/* ISO reference */}
        {criterion.iso_reference && (
          <div>
            <p className="mb-2 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              <ShieldCheck className="h-3 w-3" aria-hidden="true" />
              Standard
            </p>
            <span className="inline-flex rounded-full border border-violet-100 bg-violet-50/70 px-3 py-1 text-xs font-medium text-violet-700">
              {criterion.iso_reference}
            </span>
          </div>
        )}

        {/* Details */}
        {criterion.details && Object.keys(criterion.details).length > 0 && (
          <div>
            <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Technical details
            </p>
            <pre className="max-h-48 overflow-auto rounded-2xl border border-slate-800 bg-slate-950 p-4 text-xs leading-6 text-emerald-200">
              {JSON.stringify(criterion.details, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}