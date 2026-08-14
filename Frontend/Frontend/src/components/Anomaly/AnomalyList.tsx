// components/anomaly/AnomalyList.tsx
import type { Anomaly } from "../../types/anomaly";
import AnomalyCard from "./AnomalyCard";
import { filterAnomalies } from "../../utils/anomalyUtils";
import type { AnomalySeverity, AnomalyStatus } from "../../types/anomaly";

interface AnomalyListProps {
  anomalies:      Anomaly[];
  selected:       Anomaly | null;
  filterSeverity: AnomalySeverity | "all";
  filterStatus:   AnomalyStatus   | "all";
  search:         string;
  onSelect:       (a: Anomaly) => void;
  onAcknowledge:  (id: number) => void;
  onResolve:      (id: number) => void;
  onIgnore:       (id: number) => void;
}

export default function AnomalyList({
  anomalies, selected, filterSeverity, filterStatus, search,
  onSelect, onAcknowledge, onResolve, onIgnore,
}: AnomalyListProps) {
  const filtered = filterAnomalies(anomalies, filterSeverity, filterStatus, search);

  if (!filtered.length) {
    return (
      <div className="rounded-3xl border border-slate-200 bg-white p-10 text-center text-sm text-slate-400">
        {anomalies.length === 0 ? "No anomalies detected." : "No anomalies match your filters."}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {filtered.map(a => (
        <AnomalyCard
          key           = {a.id}
          anomaly       = {a}
          isSelected    = {selected?.id === a.id}
          onSelect      = {onSelect}
          onAcknowledge = {onAcknowledge}
          onResolve     = {onResolve}
          onIgnore      = {onIgnore}
        />
      ))}
      <p className="text-xs text-slate-400 text-right">
        {filtered.length} / {anomalies.length} anomaly(ies)
      </p>
    </div>
  );
}