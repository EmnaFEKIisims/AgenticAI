// components/anomaly/AnomalyDetails.tsx
import type { Anomaly } from "../../types/anomaly";
import SeverityBadge from "./SeverityBadge";
import { statusLabel, statusColor, anomalyTypeLabel } from "../../utils/anomalyUtils";
import type { SuggestionsResponse } from "../../types/anomaly";

interface AnomalyDetailsProps {
  anomaly:     Anomaly;
  suggestions: SuggestionsResponse | null;
  isLoadingSuggestions: boolean;
  onClose:     () => void;
  onAcknowledge: (id: number) => void;
  onResolve:     (id: number) => void;
  onIgnore:      (id: number) => void;
}

export default function AnomalyDetails({
  anomaly, suggestions, isLoadingSuggestions,
  onClose, onAcknowledge, onResolve, onIgnore,
}: AnomalyDetailsProps) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white shadow-sm overflow-hidden">

      {/* Header */}
      <div className="flex items-start justify-between gap-3 border-b border-slate-100 p-5">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Anomaly Detail</p>
          <h3 className="mt-1 text-base font-bold text-slate-900">{anomaly.title}</h3>
          <p className="text-xs text-slate-500">{anomalyTypeLabel(anomaly.anomaly_type)}</p>
        </div>
        <button onClick={onClose}
          className="rounded-xl border border-slate-200 p-2 text-slate-400 hover:bg-slate-50 text-xs">
          ✕
        </button>
      </div>

      <div className="p-5 space-y-4">
        {/* Badges */}
        <div className="flex gap-2 flex-wrap">
          <SeverityBadge severity={anomaly.severity} />
          <span className={`rounded-full border px-2.5 py-0.5 text-xs font-semibold ${statusColor(anomaly.status)}`}>
            {statusLabel(anomaly.status)}
          </span>
        </div>

        {/* Description */}
        {anomaly.description && (
          <div>
            <p className="text-xs font-semibold text-slate-400 mb-1">Finding</p>
            <p className="text-sm text-slate-700">{anomaly.description}</p>
          </div>
        )}

        {/* Impact */}
        {anomaly.impact && (
          <div>
            <p className="text-xs font-semibold text-slate-400 mb-1">Impact</p>
            <p className="text-sm text-slate-700">{anomaly.impact}</p>
          </div>
        )}

        {/* Recommendation */}
        {anomaly.recommendation && (
          <div className="rounded-2xl border border-amber-200 bg-amber-50 p-3">
            <p className="text-xs font-semibold text-amber-700 mb-1">💡 Recommendation</p>
            <p className="text-sm text-amber-900">{anomaly.recommendation}</p>
          </div>
        )}

        {/* ISO reference */}
        {anomaly.iso_reference && (
          <span className="inline-block rounded-full border border-violet-200 bg-violet-50 px-3 py-0.5 text-xs text-violet-700">
            {anomaly.iso_reference}
          </span>
        )}

        {/* Details JSON */}
        {anomaly.details && Object.keys(anomaly.details).length > 0 && (
          <div>
            <p className="text-xs font-semibold text-slate-400 mb-1">Details</p>
            <pre className="overflow-auto rounded-2xl bg-slate-950 p-3 text-xs text-emerald-300 max-h-36">
              {JSON.stringify(anomaly.details, null, 2)}
            </pre>
          </div>
        )}

        {/* HITL Actions */}
        {anomaly.status === "open" && (
          <div className="flex gap-2 pt-2 border-t border-slate-100">
            <button onClick={() => onAcknowledge(anomaly.id)}
              className="flex-1 rounded-xl border border-amber-200 bg-amber-50 py-2 text-xs font-semibold text-amber-700 hover:bg-amber-100">
              Acknowledge
            </button>
            <button onClick={() => onResolve(anomaly.id)}
              className="flex-1 rounded-xl border border-emerald-200 bg-emerald-50 py-2 text-xs font-semibold text-emerald-700 hover:bg-emerald-100">
              Resolve
            </button>
            <button onClick={() => onIgnore(anomaly.id)}
              className="flex-1 rounded-xl border border-slate-200 bg-slate-50 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100">
              Ignore
            </button>
          </div>
        )}

        {/* Suggestions / Resolution proposals */}
        {isLoadingSuggestions && (
          <p className="text-xs text-slate-400 text-center py-2">Loading suggestions…</p>
        )}
        {suggestions && suggestions.proposals.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-slate-400 mb-2">Resolution Proposals</p>
            <div className="space-y-2">
              {suggestions.proposals.map((p, i) => (
                <div key={i} className="rounded-xl border border-sky-100 bg-sky-50 p-3">
                  <p className="text-xs font-semibold text-sky-700">
                    {i + 1}. {p.action.replace(/_/g, " ")}
                  </p>
                  <p className="text-xs text-sky-800 mt-0.5">{p.description}</p>
                  {p.estimated_impact && (
                    <p className="text-xs text-sky-600 mt-0.5">→ {p.estimated_impact}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}