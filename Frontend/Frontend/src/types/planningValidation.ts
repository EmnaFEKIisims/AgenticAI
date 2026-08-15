// types/planningValidation.ts

export type HITLAction = "VALIDATE" | "REJECT" | "REQUEST_MODIFICATION";
export type HITLStatus = "idle" | "pending" | "validated" | "rejected" | "needs_revision";

export interface ValidateRequest {
  planning_group_id: string;
  validation_notes?: string;
}

export interface RejectRequest {
  planning_group_id: string;
  reason?: string;
}

export interface ValidationResponse {
  success:           boolean;
  planning_group_id: string;
  status:            string;
  total_slots:       number;
  message:           string;
  timestamp:         string;
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