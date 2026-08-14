// components/anomaly/AnomalySummary.tsx
import type { Anomaly } from "../../types/anomaly";
import { countBySeverity, countByStatus } from "../../utils/anomalyUtils";

interface AnomalySummaryProps {
  anomalies: Anomaly[];
}

export default function AnomalySummary({ anomalies }: AnomalySummaryProps) {
  const bySeverity = countBySeverity(anomalies);
  const byStatus   = countByStatus(anomalies);

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
        Anomaly Summary
      </p>

      {/* Severity row */}
      <div className="grid grid-cols-3 divide-x divide-slate-200 overflow-hidden rounded-2xl border border-slate-200">
        <div className="flex flex-col items-center p-4 bg-rose-50">
          <p className="text-3xl font-bold text-rose-600">{bySeverity.high}</p>
          <p className="text-xs text-rose-600 mt-1">🔴 High</p>
        </div>
        <div className="flex flex-col items-center p-4 bg-amber-50">
          <p className="text-3xl font-bold text-amber-600">{bySeverity.medium}</p>
          <p className="text-xs text-amber-600 mt-1">🟡 Medium</p>
        </div>
        <div className="flex flex-col items-center p-4 bg-emerald-50">
          <p className="text-3xl font-bold text-emerald-600">{bySeverity.low}</p>
          <p className="text-xs text-emerald-600 mt-1">🟢 Low</p>
        </div>
      </div>

      {/* Status row */}
      <div className="grid grid-cols-4 gap-2">
        {[
          { label: "Open",         value: byStatus.open,         color: "text-rose-600" },
          { label: "Acknowledged", value: byStatus.acknowledged, color: "text-amber-600" },
          { label: "Resolved",     value: byStatus.resolved,     color: "text-emerald-600" },
          { label: "Ignored",      value: byStatus.ignored,      color: "text-slate-400" },
        ].map(({ label, value, color }) => (
          <div key={label} className="rounded-2xl border border-slate-100 bg-slate-50 p-3 text-center">
            <p className={`text-2xl font-bold ${color}`}>{value}</p>
            <p className="text-xs text-slate-500 mt-0.5">{label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}