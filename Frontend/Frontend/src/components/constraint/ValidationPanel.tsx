import { AlertCircle, CheckCircle2, Info } from "lucide-react";
import type { ConstraintValidationResult } from "../../types/constraintTypes";

interface ValidationPanelProps {
  result: ConstraintValidationResult | null;
}

export default function ValidationPanel({ result }: ValidationPanelProps) {
  if (!result) {
    return null;
  }

  const statusLabel = result.status.toUpperCase();
  const statusStyles = {
    valid: "border-emerald-200 bg-emerald-50 text-emerald-800",
    warning: "border-amber-200 bg-amber-50 text-amber-800",
    invalid: "border-rose-200 bg-rose-50 text-rose-800",
  }[result.status];

  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-5 flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
            Validation Result
          </p>
          <h3 className="mt-1 text-xl font-bold text-slate-900">Status : {statusLabel}</h3>
        </div>
        <div className={`rounded-full border px-4 py-1 text-sm font-semibold ${statusStyles}`}>
          {statusLabel}
        </div>
      </div>

      {result.issues?.length ? (
        <div className="space-y-3">
          {result.issues.map((issue) => (
            <article key={issue.code} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="mt-0.5 h-5 w-5 text-rose-600" aria-hidden="true" />
                <div className="min-w-0">
                  <p className="font-semibold text-slate-900">❌ {issue.code}</p>
                  <p className="mt-1 text-sm text-slate-700">{issue.message}</p>
                  {issue.suggestion ? (
                    <p className="mt-2 text-sm text-slate-500">
                      <span className="font-semibold text-slate-700">Suggestion:</span> {issue.suggestion}
                    </p>
                  ) : null}
                </div>
              </div>
            </article>
          ))}
        </div>
      ) : null}

      {result.warnings?.length ? (
        <div className="mt-5 space-y-2 rounded-2xl border border-amber-200 bg-amber-50 p-4">
          {result.warnings.map((warning) => (
            <p key={warning} className="flex items-start gap-2 text-sm text-amber-900">
              <Info className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
              <span>💡 {warning}</span>
            </p>
          ))}
        </div>
      ) : null}

      {result.status === "valid" && !result.issues?.length ? (
        <div className="mt-4 flex items-center gap-2 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">
          <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
          Validation passed without blocking issues.
        </div>
      ) : null}
    </section>
  );
}
