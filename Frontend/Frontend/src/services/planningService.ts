// services/planningService.ts
// ============================
// Fix: removed fallback to relative URLs ("" / "/api").
// Always uses absolute URL pointing to http://localhost:8000.

import type {
  PlanningRunRequest,
  PlanningResponse,
  ValidateResponse,
  ConstraintsResponse,
  SessionSlot,
} from "../types/planning";

import type { PlanningDict } from "../types/constraintTypes";

// Always use an absolute URL — never relative (relative hits port 5173, not 8000)
const BASE_URL = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "")
              ?? "http://localhost:8000";

// =============================================================================
//  Base fetch helper
// =============================================================================

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body?.detail ?? detail;
    } catch {}
    throw new Error(detail);
  }

  return res.json() as Promise<T>;
}

// =============================================================================
//  Response types
// =============================================================================

export interface FullPipelineResponse {
  success:             boolean;
  total_sessions:      number;
  constraint_valid:    boolean;
  constraint_issues:   Array<{ field: string; message: string; severity: string; suggestion: string }>;
  constraint_warnings: string[];
  final_constraints:   Record<string, unknown>;
  schedule:            SessionSlot[];
}

// =============================================================================
//  MODE 1 — POST /planning/run
//  Text constraints → LLM extracts → schedule
// =============================================================================

export async function runPlanning(userConstraints?: string): Promise<PlanningResponse> {
  const body: PlanningRunRequest = {
    user_constraints: userConstraints?.trim() || undefined,
  };
  return apiFetch<PlanningResponse>("/planning/run", {
    method: "POST",
    body:   JSON.stringify(body),
  });
}

// =============================================================================
//  MODE 2 — POST /planning/run/with-constraints
//  Pre-validated planning_dict from ConstraintAgent → schedule
//  Skips ALL LLM extraction in the backend.
// =============================================================================

export async function runPlanningWithConstraints(
  constraintsDict: PlanningDict | Record<string, unknown>
): Promise<PlanningResponse> {
  return apiFetch<PlanningResponse>("/planning/run/with-constraints", {
    method: "POST",
    body:   JSON.stringify({ constraints_dict: constraintsDict }),
  });
}

// =============================================================================
//  MODE 3 — POST /planning/run/full-pipeline
//  ConstraintAgent + PlanningAgent in one single call.
// =============================================================================

export async function runFullPipeline(
  pedagogicalText: string,
  userText: string,
): Promise<FullPipelineResponse> {
  return apiFetch<FullPipelineResponse>("/planning/run/full-pipeline", {
    method: "POST",
    body:   JSON.stringify({
      pedagogical_text: pedagogicalText.trim() || "",
      user_text:        userText.trim()        || "",
    }),
  });
}

// =============================================================================
//  GET /planning/schedule
// =============================================================================

export async function getSchedule(): Promise<SessionSlot[]> {
  return apiFetch<SessionSlot[]>("/planning/schedule");
}

// =============================================================================
//  POST /planning/validate
// =============================================================================

export async function validatePlanning(): Promise<ValidateResponse> {
  return apiFetch<ValidateResponse>("/planning/validate", { method: "POST" });
}

// =============================================================================
//  GET /planning/constraints
// =============================================================================

export async function getConstraints(): Promise<ConstraintsResponse> {
  return apiFetch<ConstraintsResponse>("/planning/constraints");
}

// =============================================================================
//  GET /planning/export/csv
// =============================================================================

export async function exportCSV(): Promise<void> {
  const res = await fetch(`${BASE_URL}/planning/export/csv`);
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