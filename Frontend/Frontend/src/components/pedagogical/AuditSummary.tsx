// components/pedagogical/AuditSummary.tsx

import { CalendarDays, Clock } from "lucide-react";

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
    <div className="ped-audit-summary overflow-hidden rounded-3xl border border-blue-200 bg-blue-50/60 shadow-sm">
      <div className="p-6">
        <p className="mb-5 text-xs font-semibold uppercase tracking-wider text-slate-500">
          Audit summary
        </p>

        {/* 3-column stats */}
        <div className="grid grid-cols-3 divide-x divide-slate-100 overflow-hidden rounded-2xl border border-slate-200">
          {/* Total */}
          <div className="flex flex-col items-center justify-center bg-slate-50/60 px-4 py-5">
            <p className="text-3xl font-bold leading-none text-slate-800">{totalCriteria}</p>
            <p className="mt-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
              Criteria
            </p>
          </div>

          {/* Passed */}
          <div className="flex flex-col items-center justify-center bg-emerald-50/60 px-4 py-5">
            <p className="text-3xl font-bold leading-none text-emerald-600">{passedCriteria}</p>
            <p className="mt-1.5 text-[10px] font-semibold uppercase tracking-wider text-emerald-700">
              Compliant
            </p>
          </div>

          {/* Issues */}
          <div className="flex flex-col items-center justify-center bg-rose-50/60 px-4 py-5">
            <div className="flex flex-col items-center gap-0.5">
              {warnCount > 0 && (
                <p className="text-xs font-semibold text-amber-600">
                  {warnCount} warning{warnCount > 1 ? "s" : ""}
                </p>
              )}
              {highViolations > 0 && (
                <p className="text-xs font-semibold text-rose-600">
                  {highViolations} failure{highViolations > 1 ? "s" : ""}
                </p>
              )}
              {failedCriteria === 0 && (
                <p className="text-xs font-semibold text-emerald-600">No issues</p>
              )}
            </div>
            <p className="mt-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
              Issues
            </p>
          </div>
        </div>

        {/* Pass rate bar */}
        <div className="mt-5">
          <div className="mb-1.5 flex items-center justify-between text-[11px]">
            <span className="font-medium text-slate-500">Compliance rate</span>
            <span className="font-mono font-semibold text-slate-700">{passRate}%</span>
          </div>
          <div className="flex h-2 w-full overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full bg-emerald-500 transition-all duration-700"
              style={{ width: `${passRate}%` }}
            />
            <div
              className="h-full bg-rose-300 transition-all duration-700"
              style={{ width: `${100 - passRate}%` }}
            />
          </div>
        </div>

        {/* Context */}
        <div className="mt-5 flex items-center gap-4 border-t border-slate-100 pt-4 text-xs text-slate-500">
          <span className="inline-flex items-center gap-1.5">
            <CalendarDays className="h-3.5 w-3.5 text-slate-400" aria-hidden="true" />
            <strong className="font-semibold text-slate-700">{totalSessions}</strong>
            sessions
          </span>
          <span className="h-3 w-px bg-slate-200" />
          <span className="inline-flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5 text-slate-400" aria-hidden="true" />
            <strong className="font-semibold text-slate-700">{totalHours}h</strong>
            total
          </span>
        </div>
      </div>
    </div>
  );
}