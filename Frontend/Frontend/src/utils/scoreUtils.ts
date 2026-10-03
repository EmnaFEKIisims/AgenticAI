// utils/scoreUtils.ts
// =====================
// Pure display helpers for score and grade.
// This file does NOT calculate scores — the backend does that.
// It only transforms numbers and grades into display strings and styles.

import type { AuditGrade, CriterionSeverity } from "../types/pedagogical";

// =============================================================================
//  SCORE → LABEL
// =============================================================================

export function scoreToLabel(score: number): string {
  if (score >= 90) return "Excellent";
  if (score >= 75) return "Good";
  if (score >= 60) return "Acceptable";
  if (score >= 45) return "Needs Improvement";
  return "Non-Compliant";
}

export function scoreToEmoji(score: number): string {
  return "";
}

// =============================================================================
//  GRADE → DISPLAY
// =============================================================================

export function gradeToLabel(grade: AuditGrade): string {
  const labels: Record<AuditGrade, string> = {
    A: "Excellent",
    B: "Good",
    C: "Acceptable",
    D: "Needs Improvement",
    F: "Non-Compliant",
  };
  return labels[grade] ?? grade;
}

export function gradeToColor(grade: AuditGrade): string {
  const colors: Record<AuditGrade, string> = {
    A: "text-emerald-600",
    B: "text-sky-600",
    C: "text-amber-600",
    D: "text-orange-600",
    F: "text-rose-600",
  };
  return colors[grade] ?? "text-slate-600";
}

export function gradeToBgColor(grade: AuditGrade): string {
  const bg: Record<AuditGrade, string> = {
    A: "bg-emerald-50 border-emerald-200",
    B: "bg-sky-50     border-sky-200",
    C: "bg-amber-50   border-amber-200",
    D: "bg-orange-50  border-orange-200",
    F: "bg-rose-50    border-rose-200",
  };
  return bg[grade] ?? "bg-slate-50 border-slate-200";
}

// =============================================================================
//  SCORE → RING DEGREES  (for circular gauge, 0-360)
// =============================================================================

export function scoreToDegrees(score: number): number {
  return Math.round(Math.min(100, Math.max(0, score)) * 3.6);
}

// =============================================================================
//  SEVERITY → DISPLAY
// =============================================================================

export function severityToColor(severity: CriterionSeverity): string {
  const colors: Record<CriterionSeverity, string> = {
    high:   "text-rose-600   bg-rose-50   border-rose-200",
    medium: "text-amber-600  bg-amber-50  border-amber-200",
    low:    "text-slate-500  bg-slate-50  border-slate-200",
  };
  return colors[severity] ?? "text-slate-500";
}

export function severityToLabel(severity: CriterionSeverity): string {
  return { high: "High", medium: "Medium", low: "Low" }[severity] ?? severity;
}

// =============================================================================
//  SCORE RATIO → PROGRESS BAR WIDTH
// =============================================================================

export function ratioToWidth(ratio: number): string {
  return `${Math.round(Math.min(1, Math.max(0, ratio)) * 100)}%`;
}

// =============================================================================
//  COMPLIANCE → BADGE
// =============================================================================

export function complianceBadge(isCompliant: boolean): {
  label: string;
  className: string;
} {
  return isCompliant
    ? { label: "Compliant",     className: "bg-emerald-100 text-emerald-700 border-emerald-200" }
    : { label: "Non-Compliant", className: "bg-rose-100    text-rose-700    border-rose-200"    };
}