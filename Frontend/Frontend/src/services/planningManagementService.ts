// services/planningManagementService.ts
// Single service for HITL + Regeneration + Drag & Drop + Impact Analysis
//
// ← FIXED: validatePlanning/rejectPlanning were sending planning_group_id
//   inside the JSON body. The backend (PlanningRouter.py) takes it as a
//   PATH parameter (/planning/{planning_group_id}/validate), not a body
//   field — only { validation_notes } / { reason } belong in the body.
//   FastAPI silently dropped the extra field, so nothing broke at runtime,
//   but it no longer matched the corrected ValidateRequest/RejectRequest
//   types (types/planningValidation.ts) and was misleading about what the
//   backend actually expects.
//
// getPlanningStatus() and getMoveHistory() call endpoints
//   (/planning/{id}/status, /planning/session/{id}/history) that do not
//   exist in the PlanningRouter.py shared in this conversation. Left
//   untouched since they may live in a router file not yet reviewed —
//   verify these are backed by a real endpoint before relying on them.

import type { ValidateRequest, RejectRequest, ValidationResponse, PlanningStatusResponse } from "../types/planningValidation";
import type { RegenerateRequest, RegenerateResponse }                                       from "../types/planningRegeneration";
import type { MoveRequest, MoveResponse }                                                   from "../types/scheduleMove";
import type { ImpactRequest, ImpactResponse }                                               from "../types/impactAnalysis";

const BASE = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "")
           ?? "http://localhost:8000";

async function call<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try { const b = await res.json(); detail = b?.detail ?? detail; } catch {}
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}


// =============================================================================
//  HITL — Validate
// =============================================================================

export async function validatePlanning(
  planningGroupId: string,
  notes?: string,
): Promise<ValidationResponse> {
  const body: ValidateRequest = { validation_notes: notes };
  return call<ValidationResponse>(`/planning/${planningGroupId}/validate`, {
    method: "POST",
    body:   JSON.stringify(body),
  });
}


// =============================================================================
//  HITL — Reject
// =============================================================================

export async function rejectPlanning(
  planningGroupId: string,
  reason?: string,
): Promise<ValidationResponse> {
  const body: RejectRequest = { reason };
  return call<ValidationResponse>(`/planning/${planningGroupId}/reject`, {
    method: "POST",
    body:   JSON.stringify(body),
  });
}


// =============================================================================
//  HITL — Status
//  No matching GET /planning/{id}/status endpoint found in the router
//     shared so far. Verify before use.
// =============================================================================

export async function getPlanningStatus(planningGroupId: string): Promise<PlanningStatusResponse> {
  return call<PlanningStatusResponse>(`/planning/${planningGroupId}/status`);
}


// =============================================================================
//  Regeneration
// =============================================================================

export async function regeneratePlanning(req: RegenerateRequest): Promise<RegenerateResponse> {
  return call<RegenerateResponse>("/planning/regenerate", {
    method: "POST",
    body:   JSON.stringify(req),
  });
}


// =============================================================================
//  Impact Analysis (BEFORE applying move)
// =============================================================================

export async function analyzeImpact(
  slotId:         number,
  req:            ImpactRequest,
): Promise<ImpactResponse> {
  return call<ImpactResponse>(`/planning/session/${slotId}/impact`, {
    method: "POST",
    body:   JSON.stringify(req),
  });
}


// =============================================================================
//  Apply Move (AFTER admin confirms)
// =============================================================================

export async function moveSession(
  slotId: number,
  req:    MoveRequest,
): Promise<MoveResponse> {
  return call<MoveResponse>(`/planning/session/${slotId}/move`, {
    method: "PATCH",
    body:   JSON.stringify(req),
  });
}


// =============================================================================
//  Move History
//  No matching GET /planning/session/{id}/history endpoint found in the
//     router shared so far. Verify before use.
// =============================================================================

export async function getMoveHistory(slotId: number): Promise<{ slot_id: number; history: unknown[] }> {
  return call(`/planning/session/${slotId}/history`);
}