// components/anomaly/AnomalyCard.tsx
import type { Anomaly } from "../../types/anomaly";
import SeverityBadge from "./SeverityBadge";
import { statusLabel, statusColor, anomalyTypeLabel } from "../../utils/anomalyUtils";

interface AnomalyCardProps {
  anomaly:     Anomaly;
  isSelected:  boolean;
  onSelect:    (a: Anomaly) => void;
  onAcknowledge: (id: number) => void;
  onResolve:     (id: number) => void;
  onIgnore:      (id: number) => void;
}

export default function AnomalyCard({
  anomaly, isSelected, onSelect,
  onAcknowledge, onResolve, onIgnore,
}: AnomalyCardProps) {
  return (
    <div
      onClick={() => onSelect(anomaly)}
      className={`cursor-pointer rounded-2xl border p-4 transition ${
        isSelected
          ? "border-sky-300 bg-sky-50 ring-2 ring-sky-100"
          : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50"
      }`}
    >
      {/* Top row */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 flex-wrap">
          <SeverityBadge severity={anomaly.severity} />
          <span className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${statusColor(anomaly.status)}`}>
            {statusLabel(anomaly.status)}
          </span>
        </div>
        <p className="text-xs text-slate-400 shrink-0">
          {new Date(anomaly.detected_at).toLocaleDateString()}
        </p>
      </div>

      {/* Title + type */}
      <p className="mt-2 font-semibold text-slate-900">{anomaly.title}</p>
      <p className="text-xs text-slate-500">{anomalyTypeLabel(anomaly.anomaly_type)}</p>

      {/* Description */}
      {anomaly.description && (
        <p className="mt-2 text-sm text-slate-600 line-clamp-2">{anomaly.description}</p>
      )}

      {/* Recommendation */}
      {anomaly.recommendation && (
        <p className="mt-2 rounded-xl bg-amber-50 border border-amber-200 px-3 py-2 text-xs text-amber-800">
          💡 {anomaly.recommendation}
        </p>
      )}

      {/* ISO reference */}
      {anomaly.iso_reference && (
        <span className="mt-2 inline-block rounded-full border border-violet-200 bg-violet-50 px-2.5 py-0.5 text-xs text-violet-700">
          {anomaly.iso_reference}
        </span>
      )}

      {/* HITL Actions — only for OPEN anomalies */}
      {anomaly.status === "open" && (
        <div className="mt-3 flex gap-2" onClick={e => e.stopPropagation()}>
          <button onClick={() => onAcknowledge(anomaly.id)}
            className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-1.5 text-xs font-medium text-amber-700 hover:bg-amber-100">
            Acknowledge
          </button>
          <button onClick={() => onResolve(anomaly.id)}
            className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-700 hover:bg-emerald-100">
            Resolve
          </button>
          <button onClick={() => onIgnore(anomaly.id)}
            className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100">
            Ignore
          </button>
        </div>
      )}
    </div>
  );
}