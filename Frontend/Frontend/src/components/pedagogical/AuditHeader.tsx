// components/pedagogical/AuditHeader.tsx
// ========================================
// Displays planning context and the main "Audit Planning" button.
// When user clicks → triggers the audit.

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
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-4">

        {/* Left — titles */}
        <div>
          <div className="flex items-center gap-2">
            <span className="text-2xl">📋</span>
            <h1 className="text-xl font-bold text-slate-900">Pedagogical Audit</h1>
          </div>
          <p className="mt-1 text-sm text-slate-500">
            ISO 21001:2018 · ISO 29993:2017
          </p>
        </div>

        {/* Right — planning context */}
        {(groupName || planningId) && (
          <div className="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3 text-right">
            {groupName && (
              <p className="text-sm font-semibold text-slate-800">{groupName}</p>
            )}
            {planningId && (
              <p className="text-xs text-slate-500">Planning #{planningId}</p>
            )}
            {totalSessions > 0 && (
              <p className="text-xs text-slate-400">
                {totalSessions} sessions · {totalHours}h total
              </p>
            )}
          </div>
        )}
      </div>

      {/* Action buttons */}
      <div className="mt-5 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={onAudit}
          disabled={isLoading || !canAudit}
          className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isLoading ? (
            <>
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              Auditing…
            </>
          ) : (
            <>▶ Audit Planning</>
          )}
        </button>

        {hasReport && (
          <button
            type="button"
            onClick={onReset}
            disabled={isLoading}
            className="rounded-xl border border-slate-200 bg-white px-5 py-2.5 text-sm font-semibold text-slate-600 transition hover:bg-slate-50 disabled:opacity-60"
          >
            ✕ Reset
          </button>
        )}
      </div>

      {/* ISO badge row */}
      <div className="mt-4 flex gap-2">
        {["ISO 21001:2018", "ISO 29993:2017"].map(ref => (
          <span
            key={ref}
            className="rounded-full border border-violet-200 bg-violet-50 px-3 py-0.5 text-xs font-medium text-violet-700"
          >
            {ref}
          </span>
        ))}
      </div>
    </div>
  );
}