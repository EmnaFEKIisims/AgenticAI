// types/planning.ts
// ==================
// TypeScript types matching the backend models and API responses exactly.
// Based on:
//   - ScheduleSlot      (models/schedule.py)
//   - PlanningRouter     (api/PlanningRouter.py)

// =============================================================================
//  CORE ENTITY — ScheduleSlot  (mirrors models/schedule.py)
// =============================================================================

export type SlotStatus = "draft" | "validated" | "rejected" | "superseded";

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
//
//  ← EXTENDED: now carries the real backend truth (id/status/times), matching
//    what PlanningRouter.py's SessionSlotOut actually sends. Previously this
//    type had no id/status/start_time/end_time/is_validated, which forced
//    PlanningPage to hardcode those fields to "draft"/false/"" every time it
//    re-derived localSchedule from state.schedule — silently discarding real
//    move and validation data. That was the root cause of the "planning
//    reverts to initial state" bug.
// =============================================================================

export interface SessionSlot {
  id?:                     number;
  // ← ADDED: every session now carries its own group id from the backend
  //   (PlanningRouter.py SessionSlotOut.planning_group_id), so the frontend
  //   can derive the current planning_group_id directly from the loaded
  //   schedule instead of trusting navigation state (which was found to
  //   silently drop this field) or the ephemeral backend _last_group_id
  //   global (wiped on every backend restart).
  planning_group_id?:      string;
  session_number:          number;
  course_id:               number;
  course_title:            string;
  trainer_id:              number;
  trainer_name:            string;
  room_id:                 number;
  room_name:               string;
  group_id:                number;
  group_name:              string;
  suggested_day:           string;   // e.g. "Week 1 — Monday"
  suggested_time:          string;   // e.g. "08:00 → 11:00"
  reasoning:                string;   // agent justification

  // ← ADDED: real backend fields, previously dropped on the floor
  start_time:              string;   // ISO 8601
  end_time:                string;   // ISO 8601
  status:                  SlotStatus;
  is_validated:            boolean;
  quality_score:           number;
  pedagogical_audit_score: number;
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

// ← FIXED: this type was written for a response shape
//   (db_constraints/user_constraints) that neither /planning/run nor
//   /planning/run/with-constraints actually returns — both endpoints
//   respond with PlanningRunResponse (PlanningRouter.py), which has
//   planning_group_id and engine instead. Confirmed as the root cause of
//   "Cannot validate: no planning group found": ConstraintPage.tsx never
//   forwarded planning_group_id into navigation state, and this type
//   didn't even declare the field, so there was nothing to catch it at
//   compile time either.
//   db_constraints/user_constraints kept as optional for backward
//   compatibility with any code still reading them (they'll simply be
//   undefined at runtime, matching the actual backend response).
export interface PlanningResponse {
  success:            boolean;
  planning_group_id:  string;
  total_sessions:     number;
  final_constraints:  Constraints;   // merged = db + user
  schedule:           SessionSlot[];
  engine:             string;        // "ortools" | "greedy"
  db_constraints?:    Constraints;   // not actually sent by the backend today
  user_constraints?:  Constraints;   // not actually sent by the backend today
}


// =============================================================================
//  API — POST /planning/{group_id}/validate
// =============================================================================

export interface ValidateResponse {
  success:   boolean;
  validated: boolean;
  message:   string;
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