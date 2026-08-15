// services/planningManagementService.ts
// Single service for HITL + Regeneration + Drag & Drop + Impact Analysis

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
  return call<ValidationResponse>(`/planning/${planningGroupId}/validate`, {
    method: "POST",
    body:   JSON.stringify({ planning_group_id: planningGroupId, validation_notes: notes }),
  });
}


// =============================================================================
//  HITL — Reject
// =============================================================================

export async function rejectPlanning(
  planningGroupId: string,
  reason?: string,
): Promise<ValidationResponse> {
  return call<ValidationResponse>(`/planning/${planningGroupId}/reject`, {
    method: "POST",
    body:   JSON.stringify({ planning_group_id: planningGroupId, reason }),
  });
}


// =============================================================================
//  HITL — Status
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
// =============================================================================

export async function getMoveHistory(slotId: number): Promise<{ slot_id: number; history: unknown[] }> {
  return call(`/planning/session/${slotId}/history`);
}