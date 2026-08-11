// components/pedagogical/AuditSummary.tsx

interface AuditSummaryProps {
  totalCriteria:  number;
  passedCriteria: number;
  failedCriteria: number;
  highViolations: number;
  totalSessions:  number;
  totalHours:     number;
}

export default function AuditSummary({
  totalCriteria, passedCriteria, failedCriteria,
  highViolations, totalSessions, totalHours,
}: AuditSummaryProps) {
  const warnCount = failedCriteria - highViolations;
  const passRate  = totalCriteria > 0
    ? Math.round((passedCriteria / totalCriteria) * 100) : 0;

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm space-y-5">
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
        Audit Summary
      </p>

      {/* 3-column card row — matches the spec table */}
      <div className="grid grid-cols-3 divide-x divide-slate-200 overflow-hidden rounded-2xl border border-slate-200">

        {/* Col 1 — Total */}
        <div className="flex flex-col items-center justify-center p-5 bg-slate-50">
          <p className="text-4xl font-bold text-slate-800">{totalCriteria}</p>
          <p className="mt-1 text-xs font-semibold text-slate-500 uppercase tracking-wider">Criteria</p>
        </div>

        {/* Col 2 — Passed */}
        <div className="flex flex-col items-center justify-center p-5 bg-emerald-50">
          <p className="text-4xl font-bold text-emerald-600">{passedCriteria}</p>
          <p className="mt-1 text-xs font-semibold text-emerald-600 uppercase tracking-wider">Compliant</p>
        </div>

        {/* Col 3 — Issues */}
        <div className="flex flex-col items-center justify-center p-5 bg-rose-50">
          <div className="space-y-0.5 text-center">
            {warnCount > 0 && (
              <p className="text-sm font-semibold text-amber-600">
                {warnCount} warning{warnCount > 1 ? "s" : ""}
              </p>
            )}
            {highViolations > 0 && (
              <p className="text-sm font-semibold text-rose-600">
                {highViolations} failure{highViolations > 1 ? "s" : ""}
              </p>
            )}
            {failedCriteria === 0 && (
              <p className="text-sm font-semibold text-emerald-600">No issues</p>
            )}
          </div>
          <p className="mt-1 text-xs font-semibold text-slate-500 uppercase tracking-wider">Issues</p>
        </div>
      </div>

      {/* Pass rate bar */}
      <div>
        <div className="mb-1 flex justify-between text-xs text-slate-400">
          <span>Compliance rate</span>
          <span className="font-semibold text-slate-600">{passRate}%</span>
        </div>
        <div className="flex h-2 w-full overflow-hidden rounded-full bg-slate-100">
          <div className="h-full bg-emerald-500 transition-all duration-700"
               style={{ width: `${passRate}%` }} />
          <div className="h-full bg-rose-400 transition-all duration-700"
               style={{ width: `${100 - passRate}%` }} />
        </div>
      </div>

      {/* Planning context */}
      <div className="flex gap-4 border-t border-slate-100 pt-4 text-xs text-slate-500">
        <span>📅 <strong className="text-slate-700">{totalSessions}</strong> sessions</span>
        <span>🕐 <strong className="text-slate-700">{totalHours}h</strong> total</span>
      </div>
    </div>
  );
}