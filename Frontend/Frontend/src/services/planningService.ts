import type {
  PlanningRunRequest,
  PlanningResponse,
  ValidateResponse,
  ConstraintsResponse,
  SessionSlot,
} from "../types/planning";

const BASE_URL = import.meta.env.VITE_API_URL ?? "/api";

// =============================================================================
//  Helper — centralised fetch with error handling
// =============================================================================

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body?.detail ?? detail;
    } catch {
      // ignore JSON parse errors
    }
    throw new Error(detail);
  }

  return res.json() as Promise<T>;
}

// =============================================================================
//  1. runPlanning  —  POST /planning/run
//     Sends optional user constraints, gets full schedule back.
// =============================================================================

export async function runPlanning(
  userConstraints?: string
): Promise<PlanningResponse> {
  const body: PlanningRunRequest = {
    user_constraints: userConstraints?.trim() || undefined,
  };
  return apiFetch<PlanningResponse>("/planning/run", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

// =============================================================================
//  2. getSchedule  —  GET /planning/schedule
//     Returns the last generated schedule stored in backend memory.
// =============================================================================

export async function getSchedule(): Promise<SessionSlot[]> {
  return apiFetch<SessionSlot[]>("/planning/schedule");
}

// =============================================================================
//  3. validatePlanning  —  POST /planning/validate
//     Marks the current schedule as validated (HITL confirmation).
// =============================================================================

export async function validatePlanning(): Promise<ValidateResponse> {
  return apiFetch<ValidateResponse>("/planning/validate", {
    method: "POST",
  });
}

// =============================================================================
//  4. getConstraints  —  GET /planning/constraints
//     Returns all constraints currently stored in the DB.
// =============================================================================

export async function getConstraints(): Promise<ConstraintsResponse> {
  return apiFetch<ConstraintsResponse>("/planning/constraints");
}

// =============================================================================
//  5. exportCSV  —  GET /planning/export/csv
//     Triggers a file download of the current schedule as CSV.
//     Does NOT use apiFetch — needs raw blob handling.
// =============================================================================

export async function exportCSV(): Promise<void> {
  const res = await fetch(`${BASE_URL}/planning/export/csv`);

  if (!res.ok) {
    throw new Error(`Export failed: HTTP ${res.status}`);
  }

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `schedule_${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}

