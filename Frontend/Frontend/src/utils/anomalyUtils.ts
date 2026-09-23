// utils/anomalyUtils.ts
// ======================
// Pure display helpers for the Anomaly Agent UI.
// No API calls, no state — only formatting.
//
// ADDED in this pass: category grouping helpers (categoryOf, categoryLabel,
// categoryIcon, groupByCategory). The DB doesn't persist a "category" column,
// so it's derived client-side from anomaly_type — mirrors the backend
// classifier's CLASSIFICATION_MAP groups (conflict / overload / compliance /
// capacity / schedule). Used by the redesigned AnomalyList to replace the
// flat "wall of cards" with collapsible sections.

import type { AnomalySeverity, AnomalyStatus, Anomaly } from "../types/anomaly";

// =============================================================================
//  SEVERITY → DISPLAY
// =============================================================================

export function severityLabel(severity: AnomalySeverity): string {
  return { high: "High", medium: "Medium", low: "Low" }[severity] ?? severity;
}

export function severityIcon(severity: AnomalySeverity): string {
  return { high: "🔴", medium: "🟡", low: "🟢" }[severity] ?? "⚪";
}

export function severityColor(severity: AnomalySeverity): string {
  return {
    high:   "text-rose-700   bg-rose-50   border-rose-200",
    medium: "text-amber-700  bg-amber-50  border-amber-200",
    low:    "text-emerald-700 bg-emerald-50 border-emerald-200",
  }[severity] ?? "text-slate-700 bg-slate-50 border-slate-200";
}

// =============================================================================
//  STATUS → DISPLAY
// =============================================================================

export function statusLabel(status: AnomalyStatus): string {
  return {
    open:         "Open",
    acknowledged: "Acknowledged",
    resolved:     "Resolved",
    ignored:      "Ignored",
  }[status] ?? status;
}

export function statusColor(status: AnomalyStatus): string {
  return {
    open:         "text-rose-700   bg-rose-50   border-rose-200",
    acknowledged: "text-amber-700  bg-amber-50  border-amber-200",
    resolved:     "text-emerald-700 bg-emerald-50 border-emerald-200",
    ignored:      "text-slate-500  bg-slate-100 border-slate-200",
  }[status] ?? "text-slate-500 bg-slate-100 border-slate-200";
}

// =============================================================================
//  ANOMALY TYPE → DISPLAY
// =============================================================================

export function anomalyTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    trainer_conflict:           "Trainer Conflict",
    room_conflict:              "Room Conflict",
    learner_conflict:           "Learner Group Conflict",
    equipment_conflict:         "Equipment Conflict",
    teacher_overload:           "Trainer Overload",
    workload_exceeded:          "Workload Exceeded",
    wrong_progression:          "Wrong Progression",
    practice_before_theory:     "Practice Before Theory",
    room_capacity_insufficient: "Room Too Small",
    wrong_room_type:            "Wrong Room Type",
    prerequisite_violated:      "Prerequisite Violated",
    evaluation_misplaced:       "Evaluation Misplaced",
    insufficient_break:         "Insufficient Break",
    other:                      "Other",
  };
  return labels[type] ?? type.replace(/_/g, " ");
}

// =============================================================================
//  CATEGORY GROUPING (new)
// =============================================================================

export type AnomalyCategory = "conflict" | "overload" | "compliance" | "capacity" | "schedule" | "other";

const CATEGORY_MAP: Record<string, AnomalyCategory> = {
  trainer_conflict:           "conflict",
  room_conflict:              "conflict",
  learner_conflict:           "conflict",
  equipment_conflict:         "conflict",
  teacher_overload:           "overload",
  workload_exceeded:          "overload",
  wrong_progression:          "compliance",
  practice_before_theory:     "compliance",
  prerequisite_violated:      "compliance",
  evaluation_misplaced:       "compliance",
  room_capacity_insufficient: "capacity",
  wrong_room_type:            "capacity",
  insufficient_break:         "schedule",
};

export function categoryOf(type: string): AnomalyCategory {
  return CATEGORY_MAP[type] ?? "other";
}

export function categoryLabel(category: AnomalyCategory): string {
  return {
    conflict:   "Conflicts",
    overload:   "Overload",
    compliance: "Pedagogical Compliance",
    capacity:   "Room & Capacity",
    schedule:   "Scheduling",
    other:      "Other",
  }[category];
}

export function categoryIcon(category: AnomalyCategory): string {
  return {
    conflict:   "⚡",
    overload:   "📈",
    compliance: "🎓",
    capacity:   "🏫",
    schedule:   "🕒",
    other:      "❓",
  }[category];
}

/**
 * Groups anomalies by category, sorted so that categories containing an
 * open HIGH-severity anomaly come first — the list should auto-surface
 * what matters most instead of burying it in insertion order.
 */
export function groupByCategory(anomalies: Anomaly[]): { category: AnomalyCategory; items: Anomaly[] }[] {
  const groups = new Map<AnomalyCategory, Anomaly[]>();
  for (const a of anomalies) {
    const cat = categoryOf(a.anomaly_type);
    if (!groups.has(cat)) groups.set(cat, []);
    groups.get(cat)!.push(a);
  }

  const hasOpenHigh = (items: Anomaly[]) =>
    items.some((a) => a.severity === "high" && a.status === "open");

  return Array.from(groups.entries())
    .map(([category, items]) => ({ category, items }))
    .sort((a, b) => {
      const aCritical = hasOpenHigh(a.items) ? 1 : 0;
      const bCritical = hasOpenHigh(b.items) ? 1 : 0;
      if (aCritical !== bCritical) return bCritical - aCritical;
      return b.items.length - a.items.length;
    });
}

// =============================================================================
//  FILTERS
// =============================================================================

export function filterAnomalies(
  anomalies:      Anomaly[],
  filterSeverity: string,
  filterStatus:   string,
  search:         string,
): Anomaly[] {
  return anomalies.filter((a) => {
    if (filterSeverity !== "all" && a.severity !== filterSeverity) return false;
    if (filterStatus   !== "all" && a.status   !== filterStatus)   return false;
    if (search.trim()) {
      const q = search.toLowerCase();
      if (
        !a.title.toLowerCase().includes(q) &&
        !(a.description ?? "").toLowerCase().includes(q)
      ) return false;
    }
    return true;
  });
}

// =============================================================================
//  COUNTS
// =============================================================================

export function countBySeverity(anomalies: Anomaly[]) {
  return {
    high:   anomalies.filter(a => a.severity === "high").length,
    medium: anomalies.filter(a => a.severity === "medium").length,
    low:    anomalies.filter(a => a.severity === "low").length,
  };
}

export function countByStatus(anomalies: Anomaly[]) {
  return {
    open:         anomalies.filter(a => a.status === "open").length,
    acknowledged: anomalies.filter(a => a.status === "acknowledged").length,
    resolved:     anomalies.filter(a => a.status === "resolved").length,
    ignored:      anomalies.filter(a => a.status === "ignored").length,
  };
}