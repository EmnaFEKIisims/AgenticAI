// types/planning.ts
// ==================
// TypeScript types matching the backend models and API responses exactly.
// Based on:
//   - ScheduleSlot      (models/schedule.py)
//   - planning_router   (api/planning_router.py)

// =============================================================================
//  CORE ENTITY — ScheduleSlot  (mirrors models/schedule.py)
// =============================================================================

export type SlotStatus = "draft" | "validated" | "rejected";

export interface ScheduleSlot {
  id:                      number;
  course_id:               number;
  trainer_id:              number;
  room_id:                 number;
  learner_group_id:        number;
  start_time:              string;   // ISO 8601  e.g. "2025-09-01T08:00:00"
  end_time:                string;   // ISO 8601  e.g. "2025-09-01T11:00:00"

  // AI generated metrics
  quality_score:           number;   // 0.0 – 1.0
  pedagogical_audit_score: number;   // 0.0 – 1.0

  // HITL (Human In The Loop) validation
  is_validated:            boolean;
  status:                  SlotStatus;
}


// =============================================================================
//  API RESPONSE — SessionSlot  (what the router returns inside PlanningResponse)
//  This is the planning-view representation (enriched with names + reasoning)
// =============================================================================

export interface SessionSlot {
  session_number: number;
  course_id:      number;
  course_title:   string;
  trainer_id:     number;
  trainer_name:   string;
  room_id:        number;
  room_name:      string;
  group_id:       number;
  group_name:     string;
  suggested_day:  string;   // e.g. "Monday"
  suggested_time: string;   // e.g. "08:00-11:00"
  reasoning:      string;   // agent justification
}


// =============================================================================
//  CONSTRAINTS — structure returned by GET /planning/constraints
// =============================================================================

export interface TrainerAvailability {
  [trainerName: string]: string;  // e.g. { "Ahmed Ben Ali": "Monday morning only" }
}

export interface Constraints {
  forbidden_days:                    string[];           // e.g. ["Friday"]
  trainer_availability:              TrainerAvailability;
  session_duration_override:         number | null;      // hours
  min_room_capacity:                 number | null;
  room_type_required:                string | null;      // e.g. "Lab"
  group_priority:                    string | null;
  no_parallel_sessions_same_group:   boolean;
  prefer_matching_specialization:    boolean;
  other:                             string[];
}


// =============================================================================
//  API — POST /planning/run
// =============================================================================

export interface PlanningRunRequest {
  user_constraints?: string;   // optional free text (English or French)
}

export interface PlanningResponse {
  success:            boolean;
  total_sessions:     number;
  db_constraints:     Constraints;   // constraints loaded from DB
  user_constraints:   Constraints;   // constraints extracted by LLM from user text
  final_constraints:  Constraints;   // merged = db + user
  schedule:           SessionSlot[];
}


// =============================================================================
//  API — POST /planning/validate
// =============================================================================

export interface ValidateResponse {
  success:   boolean;
  validated: boolean;
  message:   string;   // e.g. "Schedule validated. 12 session(s) confirmed."
}


// =============================================================================
//  API — GET /planning/constraints
// =============================================================================

export interface ConstraintsResponse {
  total:       number;
  constraints: Constraints;
}


// =============================================================================
//  UI STATE — used in React components
// =============================================================================

export type PlanningStatus =
  | "idle"          // nothing generated yet
  | "loading"       // API call in progress
  | "success"       // schedule ready to display
  | "validated"     // user validated the schedule
  | "error";        // API error

export interface PlanningState {
  status:      PlanningStatus;
  schedule:    SessionSlot[];
  constraints: Constraints | null;
  error:       string | null;
  validated:   boolean;
}