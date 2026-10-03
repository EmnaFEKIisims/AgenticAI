// components/anomaly/AnomalyList.tsx
// =====================================
// REDESIGNED: anomalies are now grouped into collapsible category sections
// (Conflicts / Overload / Pedagogical Compliance / Room & Capacity /
// Scheduling) instead of one long flat list — this was the "wall of stuff"
// the design complaint was about.
//
// Sections are sorted so the category containing an open HIGH-severity
// anomaly comes first, and only THAT kind of section starts expanded —
// everything else starts collapsed so the eye goes straight to what
// matters. AnomalyCard itself is unchanged.

import { useState, useMemo } from "react";
import type { Anomaly, AnomalySeverity, AnomalyStatus } from "../../types/anomaly";
import AnomalyCard from "./AnomalyCard";
import {
  filterAnomalies,
  groupByCategory,
  categoryLabel,
  categoryIcon,
  type AnomalyCategory,
} from "../../utils/anomalyUtils";

interface AnomalyListProps {
  anomalies:      Anomaly[];
  selected:       Anomaly | null;
  filterSeverity: AnomalySeverity | "all";
  filterStatus:   AnomalyStatus | "all";
  search:         string;
  onSelect:       (anomaly: Anomaly) => void;
  onAcknowledge:  (id: number) => void;
  onResolve:      (id: number) => void;
  onIgnore:       (id: number) => void;
}

export default function AnomalyList({
  anomalies, selected, filterSeverity, filterStatus, search,
  onSelect, onAcknowledge, onResolve, onIgnore,
}: AnomalyListProps) {
  const filtered = useMemo(
    () => filterAnomalies(anomalies, filterSeverity, filterStatus, search),
    [anomalies, filterSeverity, filterStatus, search],
  );

  const groups = useMemo(() => groupByCategory(filtered), [filtered]);

  const hasOpenHigh = (items: Anomaly[]) =>
    items.some((a) => a.severity === "high" && a.status === "open");

  const [collapsed, setCollapsed] = useState<Set<AnomalyCategory>>(new Set());

  const toggle = (cat: AnomalyCategory) => {
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(cat)) next.delete(cat); else next.add(cat);
      return next;
    });
  };

  if (filtered.length === 0) {
    return (
      <div className="rounded-3xl border border-slate-200 bg-white p-10 text-center">
        <p className="text-3xl mb-3">No results</p>
        <p className="text-sm font-semibold text-slate-700">No anomalies match these filters</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {groups.map(({ category, items }) => {
        // Auto-expand only sections with an open critical anomaly, unless the
        // user manually toggled this section.
        const defaultOpen = hasOpenHigh(items);
        const isOpen = collapsed.has(category) ? !defaultOpen : defaultOpen;
        const openOverride = collapsed.has(category) ? !defaultOpen : defaultOpen;

        return (
          <div key={category} className="rounded-3xl border border-slate-200 bg-white overflow-hidden">
            <button
              onClick={() => toggle(category)}
              className="w-full flex items-center justify-between px-5 py-3.5 hover:bg-slate-50"
            >
              <div className="flex items-center gap-2.5">
                <span className="text-lg">{categoryIcon(category)}</span>
                <span className="text-sm font-bold text-slate-900">{categoryLabel(category)}</span>
                <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-500">
                  {items.length}
                </span>
                {hasOpenHigh(items) && (
                  <span className="rounded-full bg-rose-50 border border-rose-200 px-2 py-0.5 text-xs font-semibold text-rose-600">
                    critical
                  </span>
                )}
              </div>
              <span className="text-slate-400 text-xs">{openOverride ? "▲ collapse" : "▼ expand"}</span>
            </button>

            {openOverride && (
              <div className="border-t border-slate-100 divide-y divide-slate-100">
                {items.map((a) => (
                  <div key={a.id} className="p-3">
                    <AnomalyCard
                      anomaly={a}
                      isSelected={selected?.id === a.id}
                      onSelect={() => onSelect(a)}
                      onAcknowledge={onAcknowledge}
                      onResolve={onResolve}
                      onIgnore={onIgnore}
                    />
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}