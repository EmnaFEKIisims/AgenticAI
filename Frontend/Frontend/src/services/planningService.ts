/// <reference types="vite/client" />
// src/services/planningService.ts
// Updated: uses central apiFetch → X-User-ID header auto-injected

import { apiGet, apiPost, apiFetch, BASE } from "./api";

import type {
  PlanningResponse,
  ConstraintsResponse,
  SessionSlot,
} from "../types/planning";

import type { PlanningDict } from "../types/constraintTypes";

export interface FullPipelineResponse {
  success:             boolean;
  total_sessions:      number;
  constraint_valid:    boolean;
  constraint_issues:   Array<{ field: string; message: string; severity: string; suggestion: string }>;
  constraint_warnings: string[];
  final_constraints:   Record<string, unknown>;
  schedule:            SessionSlot[];
  planning_group_id:   string;
}

// POST /planning/run
export async function runPlanning(userConstraints?: string): Promise<PlanningResponse> {
  return apiPost<PlanningResponse>("/planning/run", {
    user_constraints: userConstraints?.trim() || undefined,
  });
}

// POST /planning/run/with-constraints
export async function runPlanningWithConstraints(
  constraintsDict: PlanningDict | Record<string, unknown>
): Promise<PlanningResponse> {
  return apiPost<PlanningResponse>("/planning/run/with-constraints", {
    constraints_dict: constraintsDict,
  });
}

// POST /planning/run/full-pipeline
export async function runFullPipeline(
  pedagogicalText: string,
  userText:        string,
): Promise<FullPipelineResponse> {
  return apiPost<FullPipelineResponse>("/planning/run/full-pipeline", {
    pedagogical_text: pedagogicalText.trim() || "",
    user_text:        userText.trim()        || "",
  });
}

// GET /planning/schedule
export async function getSchedule(): Promise<SessionSlot[]> {
  return apiGet<SessionSlot[]>("/planning/schedule");
}

// GET /planning/constraints
export async function getConstraints(): Promise<ConstraintsResponse> {
  return apiGet<ConstraintsResponse>("/planning/constraints");
}

// GET /planning/export/csv
export async function exportCSV(): Promise<void> {
  const res = await apiFetch("/planning/export/csv");
  if (!res.ok) throw new Error(`Export failed: HTTP ${res.status}`);

  const blob   = await res.blob();
  const url    = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href     = url;
  anchor.download = `schedule_${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}