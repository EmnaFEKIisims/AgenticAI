// types/planningRegeneration.ts

export interface RegenerateRequest {
  constraints_dict?:  Record<string, unknown>;
  user_constraints?:  string;
  rejected_group_id?: string;
  attempt:            number;
}

/** ← FIXED: matches PlanningRouter.py regenerate_planning() actual return
 *  shape (PlanningRunResponse). The previous version declared `attempt`
 *  and `message` fields that the backend never sends. */
export interface RegenerateResponse {
  success:           boolean;
  planning_group_id: string;
  total_sessions:    number;
  engine:            string;         // "ortools" | "greedy"
  final_constraints: Record<string, unknown>;
  schedule:          SessionSlotOut[];
}

// Inline type to avoid circular import
export interface SessionSlotOut {
  id?:                     number;
  // ← ADDED: matches PlanningRouter.py SessionSlotOut.planning_group_id
  planning_group_id?:      string;
  session_number:          number;
  course_id:               number;
  course_title:            string;
  trainer_id:              number;
  trainer_name:            string;
  room_id:                 number;
  room_name:               string;
  group_name:              string;
  learner_group_id:        number;
  suggested_day:           string;
  suggested_time:          string;
  start_time:              string;
  end_time:                string;
  status:                  string;
  is_validated:            boolean;
  quality_score:           number;
  pedagogical_audit_score: number;
  reasoning:               string;
}