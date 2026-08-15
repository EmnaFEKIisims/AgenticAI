// services/constraintService.ts
// ================================
// Fixed: always uses direct URL to backend (no Vite proxy).
// Set VITE_API_URL=http://localhost:8000 in frontend/.env

import type {
  ConstraintValidationResult,
  ConstraintSummaryData,
  ValidationIssue,
  ConstraintAnalyzeResponse,
  PlanningDict,
} from "../types/constraintTypes";

// ── FIXED: always direct to backend, never through Vite proxy ──────────────
// Vite proxy causes ECONNREFUSED and 502 errors when LLM takes > 30s.
// VITE_API_URL must be set in frontend/.env : VITE_API_URL=http://localhost:8000
const BASE_URL = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "")
              ?? "http://localhost:8000";   // ← fallback direct (was "/api" — wrong)


// =============================================================================
//  Base fetch helper
// =============================================================================

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${BASE_URL}${path}`;

  let res: Response;
  try {
    res = await fetch(url, {
      headers: { "Content-Type": "application/json", ...options.headers },
      ...options,
    });
  } catch (networkError) {
    // Connection refused, network down, etc.
    throw new Error(
      `Cannot reach backend at ${BASE_URL}. ` +
      `Make sure uvicorn is running: uvicorn main:app --reload`
    );
  }

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
//  1. analyzeConstraints  →  POST /constraints/analyze
// =============================================================================

export async function analyzeConstraints(
  pedagogicalText: string,
  userText: string,
): Promise<ConstraintAnalyzeResponse> {
  return apiFetch<ConstraintAnalyzeResponse>("/constraints/analyze", {
    method: "POST",
    body: JSON.stringify({
      pedagogical_text: pedagogicalText.trim() || "",
      user_text:        userText.trim()        || "",
    }),
  });
}


// =============================================================================
//  2. getISOConstraints  →  GET /constraints/iso
// =============================================================================

export async function getISOConstraints(): Promise<{
  total:       number;
  constraints: Array<{
    constraint_type: string;
    value:           unknown;
    severity:        string;
    description:     string;
  }>;
}> {
  return apiFetch("/constraints/iso");
}


// =============================================================================
//  MAPPERS  (unchanged)
// =============================================================================

export function mapValidationResult(
  backendValidation: ConstraintAnalyzeResponse["validation"],
): ConstraintValidationResult {
  return {
    status:   backendValidation.status as ConstraintValidationResult["status"],
    is_valid: backendValidation.is_valid,
    warnings: backendValidation.warnings ?? [],
    issues:   backendValidation.issues.map((i): ValidationIssue => ({
      code:       i.field,
      message:    i.message,
      severity:   i.severity as ValidationIssue["severity"],
      suggestion: i.suggestion,
    })),
  };
}

export function mapSummaryData(dict: PlanningDict): ConstraintSummaryData {
  const trainerAvailability = Object.entries(dict.trainer_availability || {}).map(
    ([trainer, avail]) => ({ trainer, availability: [avail as string] })
  );

  const planningParameters: Array<{ label: string; value: string }> = [];
  if (dict.session_duration_override != null)
    planningParameters.push({ label: "Session Duration",     value: `${dict.session_duration_override} min` });
  if (dict.sessions_per_day != null)
    planningParameters.push({ label: "Sessions per Day",     value: String(dict.sessions_per_day) });
  if (dict.break_between_sessions_minutes != null)
    planningParameters.push({ label: "Break",                value: `${dict.break_between_sessions_minutes} min` });
  if (dict.lunch_break_after_n_sessions != null)
    planningParameters.push({ label: "Lunch after",          value: `${dict.lunch_break_after_n_sessions} sessions` });
  if (dict.lunch_break_duration_minutes != null)
    planningParameters.push({ label: "Lunch Duration",       value: `${dict.lunch_break_duration_minutes} min` });
  if (dict.day_start_time != null)
    planningParameters.push({ label: "Start Time",           value: dict.day_start_time });
  if (dict.min_room_capacity != null)
    planningParameters.push({ label: "Min Room Capacity",    value: String(dict.min_room_capacity) });
  if (dict.room_type_required != null)
    planningParameters.push({ label: "Room Type",            value: dict.room_type_required });
  if (dict.group_priority != null)
    planningParameters.push({ label: "Group Priority",       value: dict.group_priority });
  if (dict.no_parallel_sessions_same_group)
    planningParameters.push({ label: "No Parallel Sessions", value: "Yes" });

  return {
    forbiddenDays:       dict.forbidden_days ?? [],
    trainerAvailability,
    planningParameters,
    pedagogicalRules:    (dict.other ?? []).filter(
      (r: unknown): r is string => typeof r === "string" && r.length > 0
    ),
  };
}