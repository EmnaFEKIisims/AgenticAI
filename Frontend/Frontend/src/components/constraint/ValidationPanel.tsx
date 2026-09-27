import { AlertTriangle, CheckCircle2, Info, ShieldCheck, XCircle } from "lucide-react";
import type { ConstraintValidationResult } from "../../types/constraintTypes";

interface ValidationPanelProps {
  result: ConstraintValidationResult | null;
}

const STATUS_CONFIG = {
  valid: {
    icon: CheckCircle2,
    label: "Valid",
    color: "text-emerald-600",
    iconBg: "bg-emerald-50 border-emerald-100 text-emerald-600",
    badge: "border-emerald-200 bg-emerald-50 text-emerald-700",
  },
  warning: {
    icon: AlertTriangle,
    label: "Warning",
    color: "text-amber-600",
    iconBg: "bg-amber-50 border-amber-100 text-amber-600",
    badge: "border-amber-200 bg-amber-50 text-amber-700",
  },
  conflict: {
    icon: AlertTriangle,
    label: "Conflict",
    color: "text-orange-600",
    iconBg: "bg-orange-50 border-orange-100 text-orange-600",
    badge: "border-orange-200 bg-orange-50 text-orange-700",
  },
  invalid: {
    icon: XCircle,
    label: "Invalid",
    color: "text-rose-600",
    iconBg: "bg-rose-50 border-rose-100 text-rose-600",
    badge: "border-rose-200 bg-rose-50 text-rose-700",
  },
} as const;

export default function ValidationPanel({ result }: ValidationPanelProps) {
  if (!result) return null;

  const config = STATUS_CONFIG[result.status];
  const StatusIcon = config.icon;

  return (
    <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <header className="flex items-center gap-4 border-b border-slate-100 bg-linear-to-br from-slate-50 via-white to-white px-6 py-6 sm:px-8">
        <span className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border ${config.iconBg} shadow-sm`}>
          <StatusIcon className="h-5 w-5" aria-hidden="true" />
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="text-lg font-semibold tracking-tight text-slate-900">
            Validation result
          </h3>
          <p className="mt-0.5 text-sm text-slate-500">
            Constraint analysis and rule-checking summary.
          </p>
        </div>
        <span className={`shrink-0 rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide ${config.badge}`}>
          {config.label}
        </span>
      </header>

      <div className="space-y-4 bg-slate-50/40 p-6 sm:p-8">
        {result.issues?.length ? (
          <div className="space-y-2.5">
            {result.issues.map((issue) => (
              <div
                key={issue.code}
                className="rounded-2xl border border-rose-100 bg-white p-4 shadow-sm"
              >
                <div className="flex items-start gap-3">
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-rose-50 text-rose-600">
                    <XCircle className="h-4 w-4" aria-hidden="true" />
                  </span>
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-rose-900">{issue.code}</p>
                    <p className="mt-1 text-sm text-slate-600">{issue.message}</p>
                    {issue.suggestion ? (
                      <p className="mt-2 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600">
                        <span className="font-semibold text-slate-700">Suggestion :</span> {issue.suggestion}
                      </p>
                    ) : null}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : null}

        {result.warnings?.length ? (
          <div className="space-y-2 rounded-2xl border border-amber-100 bg-white p-4 shadow-sm">
            {result.warnings.map((warning) => (
              <p key={warning} className="flex items-start gap-2 text-sm text-amber-900">
                <Info className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" aria-hidden="true" />
                <span>{warning}</span>
              </p>
            ))}
          </div>
        ) : null}

        {result.status === "valid" && !result.issues?.length ? (
          <div className="flex items-center gap-3 rounded-2xl border border-emerald-100 bg-white p-4 shadow-sm">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600">
              <ShieldCheck className="h-4 w-4" aria-hidden="true" />
            </span>
            <p className="text-sm text-emerald-800">
              Validation passed without blocking issues.
            </p>
          </div>
        ) : null}
      </div>
    </section>
  );
}