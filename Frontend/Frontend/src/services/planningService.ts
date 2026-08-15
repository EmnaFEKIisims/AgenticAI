// services/planningService.ts
// Fixed: removed old validatePlanning() that called /planning/validate (404)
// Validation is now handled by planningManagementService.ts → /planning/{group_id}/validate

import type {
  PlanningResponse,
  ValidateResponse,
  ConstraintsResponse,
  SessionSlot,
} from "../types/planning";

import type { PlanningDict } from "../types/constraintTypes";

const BASE_URL = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "")
              ?? "http://localhost:8000";

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      headers: { "Content-Type": "application/json", ...options.headers },
      ...options,
    });
  } catch {
    throw new Error(
      `Cannot reach backend at ${BASE_URL}. ` +
      `Make sure uvicorn is running: uvicorn main:app --reload`
    );
  }
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try { const body = await res.json(); detail = body?.detail ?? detail; } catch {}
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

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
  return apiFetch<PlanningResponse>("/planning/run", {
    method: "POST",
    body:   JSON.stringify({ user_constraints: userConstraints?.trim() || undefined }),
  });
}

// POST /planning/run/with-constraints
export async function runPlanningWithConstraints(
  constraintsDict: PlanningDict | Record<string, unknown>
): Promise<PlanningResponse> {
  return apiFetch<PlanningResponse>("/planning/run/with-constraints", {
    method: "POST",
    body:   JSON.stringify({ constraints_dict: constraintsDict }),
  });
}

// POST /planning/run/full-pipeline
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

// GET /planning/schedule
export async function getSchedule(): Promise<SessionSlot[]> {
  return apiFetch<SessionSlot[]>("/planning/schedule");
}

// GET /planning/constraints
export async function getConstraints(): Promise<ConstraintsResponse> {
  return apiFetch<ConstraintsResponse>("/planning/constraints");
}

// GET /planning/export/csv
export async function exportCSV(): Promise<void> {
  let res: Response;
  try {
    res = await fetch(`${BASE_URL}/planning/export/csv`);
  } catch {
    throw new Error("Cannot reach backend for CSV export.");
  }
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