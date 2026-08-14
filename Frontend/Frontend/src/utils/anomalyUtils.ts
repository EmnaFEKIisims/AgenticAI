// utils/anomalyUtils.ts
// ======================
// Pure display helpers for the Anomaly Agent UI.
// No API calls, no state — only formatting.

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