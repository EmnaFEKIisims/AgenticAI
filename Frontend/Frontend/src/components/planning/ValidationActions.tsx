// components/planning/ValidationActions.tsx
// =============================================
// Three HITL buttons: Validate | Reject | Request Modification

import type { HITLStatus } from "../../types/planningValidation";

interface ValidationActionsProps {
  status:        HITLStatus;
  totalSessions: number;
  attempt:       number;
  loading:       boolean;
  onValidate:    () => void;
  onReject:      () => void;
  onModify:      () => void;
}

export default function ValidationActions({
  status, totalSessions, attempt, loading,
  onValidate, onReject, onModify,
}: ValidationActionsProps) {

  const statusConfig = {
    idle:          { icon: "⏸",  label: "No planning generated",   color: "border-slate-200 bg-slate-50" },
    pending:       { icon: "⏳",  label: "Awaiting your decision",  color: "border-amber-200 bg-amber-50" },
    validated:     { icon: "",  label: "Planning validated",       color: "border-emerald-200 bg-emerald-50" },
    rejected:      { icon: "",  label: "Planning rejected",        color: "border-rose-200 bg-rose-50" },
    needs_revision:{ icon: "",  label: "Revision in progress",    color: "border-violet-200 bg-violet-50" },
  }[status] ?? { icon: "⏸", label: status, color: "border-slate-200 bg-slate-50" };

  return (
    <div className={`rounded-3xl border p-5 shadow-sm ${statusConfig.color}`}>
      <div className="flex flex-wrap items-center justify-between gap-4">

        {/* Left — status info */}
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xl">{statusConfig.icon}</span>
            <p className="font-bold text-slate-900">{statusConfig.label}</p>
          </div>
          {totalSessions > 0 && (
            <p className="mt-0.5 text-sm text-slate-600">
              {totalSessions} sessions · Proposal #{attempt}
            </p>
          )}
        </div>

        {/* Right — actions (only when pending) */}
        {status === "pending" && (
          <div className="flex flex-wrap gap-3">
            <button onClick={onValidate} disabled={loading}
              className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-60 transition">
              Validate
            </button>
            <button onClick={onModify} disabled={loading}
              className="inline-flex items-center gap-2 rounded-xl border border-violet-300 bg-violet-100 px-5 py-2.5 text-sm font-semibold text-violet-800 hover:bg-violet-200 disabled:opacity-60 transition">
              Request modification
            </button>
            <button onClick={onReject} disabled={loading}
              className="inline-flex items-center gap-2 rounded-xl border border-rose-300 bg-rose-100 px-5 py-2.5 text-sm font-semibold text-rose-800 hover:bg-rose-200 disabled:opacity-60 transition">
              Reject
            </button>
          </div>
        )}
      </div>
    </div>
  );
}