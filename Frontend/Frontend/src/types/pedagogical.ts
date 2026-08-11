// types/pedagogical.ts
// ======================
// All TypeScript types for the Pedagogical Agent frontend.
// Mirrors the backend AuditReport + CriterionReport Pydantic models.

// =============================================================================
//  ENUMS
// =============================================================================

export type AuditGrade = "A" | "B" | "C" | "D" | "F";

export type CriterionStatus = "PASSED" | "FAILED";

export type CriterionSeverity = "high" | "medium" | "low";

export type AuditStatus = "idle" | "loading" | "success" | "error";

// =============================================================================
//  ONE CRITERION  (maps to CriterionReport from backend)
// =============================================================================

export interface CriterionResult {
  rule:           string;
  status:         CriterionStatus;
  passed:         boolean;
  score:          number;
  weight:         number;
  score_ratio:    number;          // 0.0 → 1.0
  severity:       CriterionSeverity;
  message:        string;
  recommendation: string;
  iso_reference:  string;
  details:        Record<string, unknown>;
}

// =============================================================================
//  AUDIT REPORT  (maps to AuditReportOut from backend)
// =============================================================================

export interface AuditReport {
  score:           number;         // 0-100
  max_score:       number;         // 100
  score_label:     string;         // "87.5/100"
  grade:           AuditGrade;     // "A" | "B" | ...
  is_compliant:    boolean;
  compliance_rate: number;         // % of criteria passed

  total_criteria:  number;
  passed_criteria: number;
  failed_criteria: number;
  high_violations: number;         // HIGH severity failures

  planning_id:     number | null;
  group_name:      string | null;
  total_sessions:  number;
  total_hours:     number;

  iso_references:  string[];       // ["ISO 21001:2018", "ISO 29993:2017"]
  criteria:        CriterionResult[];
  recommendations: string[];
}

// =============================================================================
//  API REQUEST  (what we send to POST /audit)
// =============================================================================

export interface AuditRequest {
  schedule?:    Record<string, unknown>[];    // from PlanningAgent output
  sessions?:    SessionInput[];              // direct input
  planning_id?: number;
  group_name?:  string;
}

export interface SessionInput {
  course:        string;
  teacher:       string;
  room:          string;
  day:           string;
  start:         string;
  end:           string;
  session_type?: "theory" | "practice" | "evaluation" | "project" | "workshop" | "review" | "other";
  difficulty?:   "easy" | "medium" | "hard";
  room_type?:    "classroom" | "lab" | "workshop" | "amphitheater" | "virtual" | "other";
  prerequisites?: string[];
  group?:        string;
}

// =============================================================================
//  HOOK STATE
// =============================================================================

export interface PedagogicalAuditState {
  status:  AuditStatus;
  report:  AuditReport | null;
  error:   string | null;
}

// =============================================================================
//  HELPERS  (derived display types)
// =============================================================================

export interface GradeInfo {
  grade:       AuditGrade;
  label:       string;
  color:       string;          // Tailwind text color class
  bgColor:     string;          // Tailwind bg color class
  borderColor: string;
}

export const GRADE_INFO: Record<AuditGrade, GradeInfo> = {
  A: { grade: "A", label: "Excellent",          color: "text-emerald-700", bgColor: "bg-emerald-50",  borderColor: "border-emerald-200" },
  B: { grade: "B", label: "Good",               color: "text-sky-700",     bgColor: "bg-sky-50",      borderColor: "border-sky-200"     },
  C: { grade: "C", label: "Acceptable",         color: "text-amber-700",   bgColor: "bg-amber-50",    borderColor: "border-amber-200"   },
  D: { grade: "D", label: "Needs Improvement",  color: "text-orange-700",  bgColor: "bg-orange-50",   borderColor: "border-orange-200"  },
  F: { grade: "F", label: "Non-Compliant",      color: "text-rose-700",    bgColor: "bg-rose-50",     borderColor: "border-rose-200"    },
};

export const SEVERITY_LABEL: Record<CriterionSeverity, string> = {
  high:   "High",
  medium: "Medium",
  low:    "Low",
};