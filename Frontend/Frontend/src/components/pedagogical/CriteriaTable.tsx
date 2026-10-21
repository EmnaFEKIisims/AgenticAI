import { CheckCircle2, XCircle, AlertTriangle, Award } from "lucide-react";
import type { CriterionResult } from "../../types/pedagogical";
import { severityToColor } from "../../utils/scoreUtils";

interface CriteriaTableProps {
  criteria: CriterionResult[];
  onSelectCriterion?: (criterion: CriterionResult) => void;
  selectedRule?: string | null;
}

function criterionStatus(criterion: CriterionResult): {
  label: string;
  className: string;
  Icon: React.ElementType;
} {
  if (criterion.passed) {
    return {
      label: "Conforme",
      className: "border-emerald-100 bg-emerald-50 text-emerald-700",
      Icon: CheckCircle2,
    };
  }
  if (criterion.severity === "high") {
    return {
      label: "Échec",
      className: "border-rose-100 bg-rose-50 text-rose-700",
      Icon: XCircle,
    };
  }
  return {
    label: "Warning",
    className: "border-amber-100 bg-amber-50 text-amber-700",
    Icon: AlertTriangle,
  };
}

export default function CriteriaTable({
  criteria,
  onSelectCriterion,
  selectedRule,
}: CriteriaTableProps) {
  return (
    <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      {/* Header */}
      <header className="flex items-start gap-4 border-b border-slate-100 bg-linear-to-br from-slate-50 via-white to-white px-6 py-5 sm:px-8">
        <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-cyan-200 bg-cyan-100 text-cyan-700 shadow-sm">
          <Award className="h-5 w-5" aria-hidden="true" />
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="text-base font-semibold tracking-tight text-slate-900">
            Results per criterion
          </h3>
          <p className="mt-0.5 text-sm text-slate-500">
            Detailed evaluation of each audited rule.
          </p>
        </div>
        <span className="shrink-0 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-600">
          {criteria.length}
        </span>
      </header>

      {criteria.length === 0 ? (
        <div className="px-6 py-16 text-center text-sm text-slate-500">
          Aucun critère audité pour le moment.
        </div>
      ) : (
        <>
          {/* Desktop table */}
          <div className="hidden overflow-x-auto md:block">
            <table className="min-w-full divide-y divide-slate-100">
              <thead>
                <tr className="border-b border-slate-100 bg-linear-to-b from-slate-50 to-slate-50/50 text-left text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  <th className="px-5 py-3.5">Criterion</th>
                  <th className="px-5 py-3.5">Status</th>
                  <th className="px-5 py-3.5">Score</th>
                  <th className="px-5 py-3.5">Explanation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50 bg-white">
                {criteria.map((criterion) => {
                  const status = criterionStatus(criterion);
                  const ratioPct = Math.round(criterion.score_ratio * 100);
                  const isSelected = selectedRule === criterion.rule;
                  const StatusIcon = status.Icon;

                  return (
                    <tr
                      key={criterion.rule}
                      onClick={() => onSelectCriterion?.(criterion)}
                      className={`transition-colors ${
                        onSelectCriterion ? "cursor-pointer hover:bg-slate-50/60" : ""
                      } ${isSelected ? "bg-sky-50/40" : ""}`}
                    >
                      <td className="px-5 py-4 align-top">
                        <p className="font-semibold text-slate-800">{criterion.rule}</p>
                        {criterion.iso_reference && (
                          <span className="mt-2 inline-block rounded-full border border-violet-100 bg-violet-50/70 px-2.5 py-0.5 text-[10px] font-medium text-violet-700">
                            {criterion.iso_reference}
                          </span>
                        )}
                      </td>

                      <td className="px-5 py-4 align-top">
                        <div className="flex flex-col items-start gap-1.5">
                          <span
                            className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold ${status.className}`}
                          >
                            <StatusIcon className="h-3 w-3" aria-hidden="true" />
                            {status.label}
                          </span>
                          <span
                            className={`rounded-full border px-2.5 py-0.5 text-[10px] font-medium ${severityToColor(criterion.severity)}`}
                          >
                            Severity · {criterion.severity}
                          </span>
                        </div>
                      </td>

                      <td className="px-5 py-4 align-top">
                        <p className="font-mono text-sm font-semibold text-slate-800">
                          {criterion.score.toFixed(0)}
                          <span className="text-slate-400">/{criterion.weight.toFixed(0)}</span>
                        </p>
                        <p className="mt-0.5 text-[10px] font-medium text-slate-500">{ratioPct}%</p>
                        <div className="mt-2 h-1 w-28 overflow-hidden rounded-full bg-slate-100">
                          <div
                            className={`h-full rounded-full ${
                              criterion.passed ? "bg-emerald-500" : "bg-rose-400"
                            }`}
                            style={{ width: `${ratioPct}%` }}
                          />
                        </div>
                      </td>

                      <td className="px-5 py-4 align-top">
                        <p className="line-clamp-2 max-w-xl text-sm leading-relaxed text-slate-600">
                          {criterion.message || "Aucune explication fournie."}
                        </p>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Mobile cards */}
          <div className="space-y-3 bg-slate-50/40 p-4 md:hidden">
            {criteria.map((criterion) => {
              const status = criterionStatus(criterion);
              const ratioPct = Math.round(criterion.score_ratio * 100);
              const isSelected = selectedRule === criterion.rule;
              const StatusIcon = status.Icon;

              return (
                <button
                  type="button"
                  key={criterion.rule}
                  onClick={() => onSelectCriterion?.(criterion)}
                  className={`w-full rounded-2xl border p-4 text-left transition ${
                    isSelected
                      ? "border-sky-200 bg-sky-50/40 ring-2 ring-sky-100"
                      : "border-slate-100 bg-white shadow-sm"
                  } ${onSelectCriterion ? "active:scale-[0.99]" : ""}`}
                >
                  <p className="font-semibold text-slate-900">{criterion.rule}</p>
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold ${status.className}`}>
                      <StatusIcon className="h-3 w-3" aria-hidden="true" />
                      {status.label}
                    </span>
                    <span className="font-mono text-xs text-slate-500">{ratioPct}%</span>
                  </div>
                  <p className="mt-2 line-clamp-2 text-sm text-slate-600">
                    {criterion.message || "Aucune explication fournie."}
                  </p>
                </button>
              );
            })}
          </div>
        </>
      )}
    </section>
  );
}