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
} {
  if (criterion.passed) {
    return {
      label: "Compliant",
      className: "border-emerald-200 bg-emerald-50 text-emerald-700",
    };
  }

  if (criterion.severity === "high") {
    return {
      label: "Failed",
      className: "border-rose-200 bg-rose-50 text-rose-700",
    };
  }

  return {
    label: "Warning",
    className: "border-amber-200 bg-amber-50 text-amber-700",
  };
}

export default function CriteriaTable({
  criteria,
  onSelectCriterion,
  selectedRule,
}: CriteriaTableProps) {
  return (
    <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 bg-slate-50/80 px-5 py-4">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
          Audited criteria
        </p>
        <h3 className="mt-1 text-lg font-bold text-slate-900">Results by criterion</h3>
      </div>

      {criteria.length === 0 ? (
        <div className="px-5 py-10 text-center text-sm text-slate-500">
          No audited criteria available at the moment.
        </div>
      ) : (
        <>
          <div className="hidden overflow-x-auto md:block">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-white">
                <tr className="text-left text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                  <th className="px-5 py-3">Criterion</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3">Score</th>
                  <th className="px-5 py-3">Explanation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {criteria.map((criterion) => {
                  const status = criterionStatus(criterion);
                  const ratioPct = Math.round(criterion.score_ratio * 100);
                  const isSelected = selectedRule === criterion.rule;

                  return (
                    <tr
                      key={criterion.rule}
                      onClick={() => onSelectCriterion?.(criterion)}
                      className={`group transition ${
                        onSelectCriterion ? "cursor-pointer hover:bg-slate-50" : ""
                      } ${isSelected ? "bg-sky-50/50" : ""}`}
                    >
                      <td className="px-5 py-4 align-top">
                        <p className="font-semibold text-slate-800">{criterion.rule}</p>
                        {criterion.iso_reference && (
                          <span className="mt-2 inline-block rounded-full border border-violet-200 bg-violet-50 px-2.5 py-0.5 text-[11px] font-medium text-violet-700">
                            {criterion.iso_reference}
                          </span>
                        )}
                      </td>

                      <td className="px-5 py-4 align-top">
                        <div className="flex flex-col items-start gap-1.5">
                          <span
                            className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${status.className}`}
                          >
                            {status.label}
                          </span>
                          <span
                            className={`rounded-full border px-2.5 py-0.5 text-[11px] font-medium ${severityToColor(criterion.severity)}`}
                          >
                            Severite {criterion.severity}
                          </span>
                        </div>
                      </td>

                      <td className="px-5 py-4 align-top">
                        <p className="text-sm font-semibold text-slate-800">
                          {criterion.score.toFixed(0)}/{criterion.weight.toFixed(0)}
                        </p>
                        <p className="text-xs text-slate-500">{ratioPct}%</p>
                        <div className="mt-2 h-1.5 w-28 overflow-hidden rounded-full bg-slate-100">
                          <div
                            className={`h-full rounded-full ${
                              criterion.passed ? "bg-emerald-500" : "bg-rose-400"
                            }`}
                            style={{ width: `${ratioPct}%` }}
                          />
                        </div>
                      </td>

                      <td className="px-5 py-4 align-top">
                        <p className="max-w-xl text-sm leading-relaxed text-slate-600 line-clamp-2">
                          {criterion.message || "No explanation provided."}
                        </p>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="space-y-3 p-4 md:hidden">
            {criteria.map((criterion) => {
              const status = criterionStatus(criterion);
              const ratioPct = Math.round(criterion.score_ratio * 100);
              const isSelected = selectedRule === criterion.rule;

              return (
                <button
                  type="button"
                  key={criterion.rule}
                  onClick={() => onSelectCriterion?.(criterion)}
                  className={`w-full rounded-2xl border p-4 text-left transition ${
                    isSelected ? "border-sky-300 bg-sky-50" : "border-slate-200 bg-white"
                  } ${onSelectCriterion ? "active:scale-[0.99]" : ""}`}
                >
                  <p className="font-semibold text-slate-900">{criterion.rule}</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    <span
                      className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${status.className}`}
                    >
                      {status.label}
                    </span>
                    <span className="text-xs text-slate-500">{ratioPct}%</span>
                  </div>
                  <p className="mt-2 text-sm text-slate-600 line-clamp-2">
                    {criterion.message || "No explanation provided."}
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
