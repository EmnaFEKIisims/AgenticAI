// components/anomaly/AnomalyHeader.tsx
// No input field, no button — page auto-loads on mount.

interface AnomalyHeaderProps {
  totalAnomalies: number;
  openCount:      number;
  hasCritical:    boolean;
  isLoading:      boolean;
}

export default function AnomalyHeader({
  totalAnomalies, openCount, hasCritical, isLoading,
}: AnomalyHeaderProps) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-4">

        <div className="flex items-center gap-3">
          <span className="text-2xl">🔍</span>
          <div>
            <h1 className="text-xl font-bold text-slate-900">Anomaly Agent</h1>
            <p className="text-sm text-slate-500">
              Detect · Classify · Resolve
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {isLoading && (
            <span className="text-xs text-slate-400 animate-pulse">
              Loading anomalies…
            </span>
          )}

          {!isLoading && totalAnomalies > 0 && (
            <>
              <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600">
                {totalAnomalies} total
              </span>
              <span className={`rounded-full border px-4 py-1 text-xs font-semibold ${
                hasCritical
                  ? "border-rose-200 bg-rose-50 text-rose-700"
                  : "border-emerald-200 bg-emerald-50 text-emerald-700"
              }`}>
                {hasCritical
                  ? `🔴 ${openCount} open — action required`
                  : "✅ No critical anomalies"}
              </span>
            </>
          )}

          {!isLoading && totalAnomalies === 0 && (
            <span className="rounded-full border border-emerald-200 bg-emerald-50 px-4 py-1 text-xs font-semibold text-emerald-700">
              ✅ No anomalies detected
            </span>
          )}
        </div>
      </div>
    </div>
  );
}