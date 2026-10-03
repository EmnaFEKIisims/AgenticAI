// components/anomaly/AnomalyHeader.tsx
// =======================================
// Light polish only: critical banner now uses the same rose/emerald language
// as the rest of the redesign, and shows a quiet "all clear" state instead
// of nothing when there's nothing open.

interface AnomalyHeaderProps {
  totalAnomalies: number;
  openCount:      number;
  hasCritical:    boolean;
  isLoading:      boolean;
}

export default function AnomalyHeader({
  totalAnomalies, openCount, hasCritical, isLoading,
}: AnomalyHeaderProps) {
  if (isLoading) return null;

  if (hasCritical) {
    return (
      <div className="rounded-2xl border border-rose-200 bg-rose-50 px-5 py-3.5 flex items-center gap-3">
        <div>
          <p className="text-sm font-bold text-rose-800">Critical anomalies detected</p>
          <p className="text-xs text-rose-600">
            {openCount} open · {totalAnomalies} total — review the flagged items below.
          </p>
        </div>
      </div>
    );
  }

  if (openCount > 0) {
    return (
      <div className="rounded-2xl border border-amber-200 bg-amber-50 px-5 py-3.5 flex items-center gap-3">
        <p className="text-sm font-semibold text-amber-800">
          {openCount} open anomal{openCount === 1 ? "y" : "ies"} to review — none critical.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-5 py-3.5 flex items-center gap-3">
      <p className="text-sm font-semibold text-emerald-800">
        All clear — no open anomalies right now.
      </p>
    </div>
  );
}