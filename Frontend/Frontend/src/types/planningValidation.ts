// types/planningValidation.ts

export type HITLAction = "VALIDATE" | "REJECT" | "REQUEST_MODIFICATION";
export type HITLStatus = "idle" | "pending" | "validated" | "rejected" | "needs_revision";

// ← FIXED: planning_group_id removed. The backend takes it as a PATH
//   parameter (POST /planning/{planning_group_id}/validate), not a body
//   field — only { validation_notes } / { reason } belong in the body.
export interface ValidateRequest {
  validation_notes?: string;
}

export interface RejectRequest {
  reason?: string;
}

/** ← FIXED: matches PlanningRouter.py validate_schedule()/reject_schedule()
 *  actual return shape ({success, hitl_status, total_slots}). The previous
 *  version declared planning_group_id/status/message/timestamp, none of
 *  which the backend sends, and was missing hitl_status, which it does. */
export interface ValidationResponse {
  success:     boolean;
  hitl_status: string;   // "validated" | "rejected"
  total_slots: number;
}

export interface PlanningStatusResponse {
  planning_group_id: string;
  status:            string;
  total_slots:       number;
  validated_slots:   number;
  rejected_slots:    number;
  draft_slots:       number;
  created_at?:       string;
  validated_at?:     string;
  rejected_at?:      string;
}