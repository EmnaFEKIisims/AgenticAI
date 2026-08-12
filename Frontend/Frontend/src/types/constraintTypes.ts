// types/constraintTypes.ts
// ==========================
// All TypeScript types for the Constraint Agent frontend.
// Matches both component props and backend API response shapes.

// =============================================================================
//  FORM
// =============================================================================

export interface ConstraintFormValue {
  pedagogicalText: string;
  userText:        string;
}

// =============================================================================
//  VALIDATION  (matches ValidationPanel.tsx props + backend /constraints/analyze)
// =============================================================================

export type ConstraintStatus = "valid" | "warning" | "conflict" | "invalid";

export interface ValidationIssue {
  code:       string;       // maps to backend "field"
  message:    string;
  severity:   "invalid" | "conflict" | "warning";
  suggestion?: string;
}

export interface ConstraintValidationResult {
  status:   ConstraintStatus;
  is_valid: boolean;
  issues:   ValidationIssue[];
  warnings: string[];
}

// =============================================================================
//  SUMMARY  (matches ConstraintSummary.tsx props)
// =============================================================================

export interface TrainerAvailabilityEntry {
  trainer:      string;
  availability: string[];
}

export interface PlanningParameter {
  label: string;
  value: string;
}

export interface ConstraintSummaryData {
  forbiddenDays:        string[];
  trainerAvailability:  TrainerAvailabilityEntry[];
  planningParameters:   PlanningParameter[];
  pedagogicalRules:     string[];
}

// =============================================================================
//  API RESPONSE  (from POST /constraints/analyze)
// =============================================================================

export interface ConstraintAnalyzeIssue {
  field: string;
  message: string;
  severity?: ValidationIssue["severity"];
  suggestion?: string;
}

export interface ConstraintAnalyzeValidation {
  status: ConstraintStatus;
  is_valid: boolean;
  issues: ConstraintAnalyzeIssue[];
  warnings?: string[];
}

export interface ConstraintAnalyzeResponse {
  success:       boolean;
  is_valid:      boolean;
  validation:    ConstraintAnalyzeValidation;
  planning_dict: PlanningDict;
  preprocessing?: {
    pedagogical?: { language: string; day_mentions: string[]; time_mentions: string[] };
    user?:        { language: string; day_mentions: string[]; time_mentions: string[] };
  };
  error?: string | null;
}

export interface PlanningDict {
  forbidden_days?:                    string[];
  trainer_availability?:              Record<string, string>;
  session_duration_override?:         number | null;
  sessions_per_day?:                  number | null;
  break_between_sessions_minutes?:    number | null;
  lunch_break_after_n_sessions?:      number | null;
  lunch_break_duration_minutes?:      number | null;
  day_start_time?:                    string | null;
  min_room_capacity?:                 number | null;
  room_type_required?:                string | null;
  group_priority?:                    string | null;
  no_parallel_sessions_same_group?:   boolean;
  prefer_matching_specialization?:    boolean;
  other?:                             string[];
}

// =============================================================================
//  HOOK STATE
// =============================================================================

export type ConstraintAgentStatus =
  | "idle"
  | "loading"
  | "success"
  | "error";

export interface ConstraintAgentState {
  status:      ConstraintAgentStatus;
  response:    ConstraintAnalyzeResponse | null;
  summary:     ConstraintSummaryData | null;
  validation:  ConstraintValidationResult | null;
  error:       string | null;
}