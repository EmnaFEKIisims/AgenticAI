// types/anomaly.ts
// ==================
// All TypeScript types for the Anomaly Agent frontend.
// Mirrors exactly the Pydantic schemas in api/AnomalyRouter.py

// =============================================================================
//  ENUMS
// =============================================================================

export type AnomalySeverity = "high" | "medium" | "low";

export type AnomalyStatus =
  | "open"
  | "acknowledged"
  | "resolved"
  | "ignored";

export type AnomalyType =
  | "trainer_conflict"
  | "room_conflict"
  | "learner_conflict"
  | "equipment_conflict"
  | "teacher_overload"
  | "workload_exceeded"
  | "wrong_progression"
  | "practice_before_theory"
  | "room_capacity_insufficient"
  | "wrong_room_type"
  | "prerequisite_violated"
  | "evaluation_misplaced"
  | "insufficient_break"
  | "other";

// =============================================================================
//  ANOMALY (from GET /anomalies/{id} and GET /anomalies/planning/{id})
// =============================================================================

export interface Anomaly {
  id:               number;
  planning_id:      number | null;
  schedule_slot_id: number | null;
  anomaly_type:     string;
  severity:         AnomalySeverity;
  status:           AnomalyStatus;
  title:            string;
  description:      string | null;
  details:          Record<string, unknown> | null;
  impact:           string | null;
  recommendation:   string | null;
  iso_reference:    string | null;
  detected_at:      string;
  resolved_at:      string | null;
}

// =============================================================================
//  ANALYZE (from POST /anomalies/analyze/{planning_id})
// =============================================================================

export interface AnalyzeRequest {
  schedule:       Record<string, unknown>[];
  groups?:        Record<string, unknown>[];
  rooms?:         Record<string, unknown>[];
  equipment_data?: Record<string, unknown>[];
  forbidden_days?: string[];
  admin_id?:      number;
}

export interface AnalyzeResponse {
  success:          boolean;
  total_detected:   number;
  high_count:       number;
  medium_count:     number;
  low_count:        number;
  has_critical:     boolean;
  summary:          string;
  anomalies:        Record<string, unknown>[];
  notification_ids: number[];
}

// =============================================================================
//  STATUS UPDATE (from PATCH /anomalies/{id}/status)
// =============================================================================

export interface StatusUpdate {
  status: "acknowledged" | "resolved" | "ignored";
}

// =============================================================================
//  SUGGESTIONS (from POST /anomalies/{id}/suggestions)
// =============================================================================

export interface Resolution {
  action:           string;
  description:      string;
  priority:         number;
  details:          Record<string, unknown>;
  estimated_impact: string;
  requires_hitl:    boolean;
}

export interface SuggestionsResponse {
  anomaly_id: number;
  proposals:  Resolution[];
}

// =============================================================================
//  IMPACT ANALYSIS (from POST /anomalies/impact-analysis)
// =============================================================================

export interface ImpactRequest {
  old_schedule:  Record<string, unknown>[];
  modified_slot: Record<string, unknown>;
  new_time:      { start_time: string; end_time: string };
  planning_id?:  number;
  groups?:       Record<string, unknown>[];
  rooms?:        Record<string, unknown>[];
}

export interface ImpactResponse {
  modified_session:   Record<string, unknown>;
  old_time:           { start_time: string; end_time: string };
  new_time:           { start_time: string; end_time: string };
  affected_slots:     Record<string, unknown>[];
  new_conflicts:      Record<string, unknown>[];
  resolved_conflicts: Record<string, unknown>[];
  summary:            string;
}

// =============================================================================
//  HOOK STATE
// =============================================================================

export type AnomalyPageStatus = "idle" | "loading" | "success" | "error";

export interface AnomalyState {
  status:   AnomalyPageStatus;
  anomalies: Anomaly[];
  selected: Anomaly | null;
  error:    string | null;
  filterSeverity: AnomalySeverity | "all";
  filterStatus:   AnomalyStatus   | "all";
}