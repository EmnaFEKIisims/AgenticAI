// components/anomaly/AnomalySummary.tsx
// ========================================
// REDESIGNED: replaces the old "grid of raw numbers" with a proportional
// severity bar (at a glance: how bad is it, not just how many) plus a
// compact status pill row. Same idiom used in the PedagogicalAuditPage
// redesign — curated "what matters" summary instead of a number dump.

import type { Anomaly } from "../../types/anomaly";
import { countBySeverity, countByStatus } from "../../utils/anomalyUtils";

interface AnomalySummaryProps {
  anomalies: Anomaly[];
}

export default function AnomalySummary({ anomalies }: AnomalySummaryProps) {
  const total = anomalies.length;
  const bySeverity = countBySeverity(anomalies);
  const byStatus = countByStatus(anomalies);

  const pct = (n: number) => (total === 0 ? 0 : Math.round((n / total) * 100));

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-5 space-y-4">

      {/* Proportional severity bar */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-400">
            Severity Breakdown
          </p>
          <p className="text-xs text-slate-400">{total} total</p>
        </div>

        <div className="flex h-3 w-full overflow-hidden rounded-full bg-slate-100">
          {bySeverity.high > 0 && (
            <div className="bg-rose-500" style={{ width: `${pct(bySeverity.high)}%` }} />
          )}
          {bySeverity.medium > 0 && (
            <div className="bg-amber-400" style={{ width: `${pct(bySeverity.medium)}%` }} />
          )}
          {bySeverity.low > 0 && (
            <div className="bg-emerald-400" style={{ width: `${pct(bySeverity.low)}%` }} />
          )}
        </div>

        <div className="mt-2 flex gap-4 text-xs">
          <span className="flex items-center gap-1.5 text-slate-600">
            <span className="h-2 w-2 rounded-full bg-rose-500" /> High · {bySeverity.high}
          </span>
          <span className="flex items-center gap-1.5 text-slate-600">
            <span className="h-2 w-2 rounded-full bg-amber-400" /> Medium · {bySeverity.medium}
          </span>
          <span className="flex items-center gap-1.5 text-slate-600">
            <span className="h-2 w-2 rounded-full bg-emerald-400" /> Low · {bySeverity.low}
          </span>
        </div>
      </div>

      {/* Status pills */}
      <div className="flex flex-wrap gap-2 pt-3 border-t border-slate-100">
        <StatusPill label="Open"         value={byStatus.open}         color="rose"    />
        <StatusPill label="Acknowledged" value={byStatus.acknowledged} color="amber"   />
        <StatusPill label="Resolved"     value={byStatus.resolved}     color="emerald" />
        <StatusPill label="Ignored"      value={byStatus.ignored}      color="slate"   />
      </div>
    </div>
  );
}

function StatusPill({
  label, value, color,
}: { label: string; value: number; color: "rose" | "amber" | "emerald" | "slate" }) {
  const styles: Record<string, string> = {
    rose:    "bg-rose-50 text-rose-700 border-rose-200",
    amber:   "bg-amber-50 text-amber-700 border-amber-200",
    emerald: "bg-emerald-50 text-emerald-700 border-emerald-200",
    slate:   "bg-slate-50 text-slate-500 border-slate-200",
  };
  return (
    <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${styles[color]}`}>
      {label} · {value}
    </span>
  );
}