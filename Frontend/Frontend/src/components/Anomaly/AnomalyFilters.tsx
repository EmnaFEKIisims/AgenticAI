// components/anomaly/AnomalyFilters.tsx
import type { AnomalySeverity, AnomalyStatus } from "../../types/anomaly";

interface AnomalyFiltersProps {
  filterSeverity:    AnomalySeverity | "all";
  filterStatus:      AnomalyStatus   | "all";
  search:            string;
  onSeverityChange:  (v: AnomalySeverity | "all") => void;
  onStatusChange:    (v: AnomalyStatus   | "all") => void;
  onSearchChange:    (v: string) => void;
}

export default function AnomalyFilters({
  filterSeverity, filterStatus, search,
  onSeverityChange, onStatusChange, onSearchChange,
}: AnomalyFiltersProps) {
  return (
    <div className="flex flex-wrap gap-3 rounded-2xl border border-slate-200 bg-white p-4">

      {/* Search */}
      <input
        type="text"
        placeholder="Search anomalies..."
        value={search}
        onChange={e => onSearchChange(e.target.value)}
        className="flex-1 min-w-40 rounded-xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm text-slate-800 outline-none focus:border-slate-400"
      />

      {/* Severity filter */}
      <select
        value={filterSeverity}
        onChange={e => onSeverityChange(e.target.value as AnomalySeverity | "all")}
        className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 outline-none"
      >
        <option value="all">All Severities</option>
        <option value="high">High</option>
        <option value="medium">Medium</option>
        <option value="low">Low</option>
      </select>

      {/* Status filter */}
      <select
        value={filterStatus}
        onChange={e => onStatusChange(e.target.value as AnomalyStatus | "all")}
        className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 outline-none"
      >
        <option value="all">All Statuses</option>
        <option value="open">Open</option>
        <option value="acknowledged">Acknowledged</option>
        <option value="resolved">Resolved</option>
        <option value="ignored">Ignored</option>
      </select>
    </div>
  );
}