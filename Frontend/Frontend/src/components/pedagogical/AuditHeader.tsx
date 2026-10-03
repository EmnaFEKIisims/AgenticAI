// components/pedagogical/AuditHeader.tsx
// ========================================
// Displays planning context and the main "Audit Planning" button.
// When user clicks → triggers the audit.

import {
  ClipboardCheck,
  Play,
  RotateCcw,
  Loader2,
  ShieldCheck,
  CalendarDays,
  Clock,
  Users,
} from "lucide-react";

interface AuditHeaderProps {
  groupName?:     string | null;
  planningId?:    number | null;
  totalSessions:  number;
  totalHours:     number;
  isLoading:      boolean;
  hasReport:      boolean;
  canAudit?:      boolean;
  onAudit:        () => void;
  onReset:        () => void;
}

export default function AuditHeader({
  groupName,
  planningId,
  totalSessions,
  totalHours,
  isLoading,
  hasReport,
  canAudit = true,
  onAudit,
  onReset,
}: AuditHeaderProps) {
  const hasContext = Boolean(groupName || planningId);

  return (
    <section className="ped-audit-card overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      {/* Header */}
      <header className="ped-audit-card-top flex flex-wrap items-start justify-between gap-4 border-b border-slate-100 bg-linear-to-br from-slate-50 via-white to-white px-6 py-6 sm:px-8">
        <div className="flex items-start gap-4">
          <span className="ped-audit-icon flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-slate-900 text-white shadow-sm">
            <ClipboardCheck className="h-5 w-5" aria-hidden="true" />
          </span>
          <div className="min-w-0">
            <h1 className="text-lg font-semibold tracking-tight text-slate-900">
              Pedagogical Audit
            </h1>
            <p className="mt-0.5 text-sm text-slate-500">
              Automated compliance check against quality standards.
            </p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {["ISO 21001:2018", "ISO 29993:2017"].map((ref) => (
                <span
                  key={ref}
                  className="inline-flex items-center gap-1 rounded-full border border-violet-100 bg-violet-50/70 px-2.5 py-0.5 text-[11px] font-medium text-violet-700"
                >
                  <ShieldCheck className="h-3 w-3" aria-hidden="true" />
                  {ref}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Planning context */}
        {hasContext && (
          <div className="ped-audit-context min-w-0 rounded-2xl border border-slate-100 bg-slate-50/60 px-4 py-3">
            {groupName && (
              <p className="flex items-center gap-2 text-sm font-semibold text-slate-800">
                <Users className="h-3.5 w-3.5 text-slate-500" aria-hidden="true" />
                {groupName}
              </p>
            )}
            {planningId && (
              <p className="mt-1 font-mono text-[11px] text-slate-400">
                Planning #{planningId}
              </p>
            )}
            {totalSessions > 0 && (
              <div className="mt-2 flex items-center gap-3 text-xs text-slate-500">
                <span className="inline-flex items-center gap-1">
                  <CalendarDays className="h-3 w-3" aria-hidden="true" />
                  {totalSessions} sessions
                </span>
                <span className="h-3 w-px bg-slate-200" />
                <span className="inline-flex items-center gap-1">
                  <Clock className="h-3 w-3" aria-hidden="true" />
                  {totalHours}h
                </span>
              </div>
            )}
          </div>
        )}
      </header>

      {/* Actions */}
      <div className="ped-audit-actions flex flex-wrap items-center gap-3 bg-white px-6 py-5 sm:px-8">
        <button
          type="button"
          onClick={onAudit}
          disabled={isLoading || !canAudit}
          className="ped-audit-primary inline-flex items-center gap-2 rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 hover:shadow disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isLoading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
              Auditing…
            </>
          ) : (
            <>
              <Play className="h-4 w-4" aria-hidden="true" />
              Audit planning
            </>
          )}
        </button>

        {hasReport && (
          <button
            type="button"
            onClick={onReset}
            disabled={isLoading}
            className="ped-audit-reset inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <RotateCcw className="h-4 w-4" aria-hidden="true" />
            Reset
          </button>
        )}
      </div>
    </section>
  );
}