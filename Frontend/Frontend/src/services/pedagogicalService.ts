// services/pedagogicalApi.ts
// ============================
// All API calls for the Pedagogical Agent.
// Communicates with:
//   POST /audit       → run audit
//   GET  /audit/rules → view active rules
//   GET  /audit/report/{id} → get cached report

import type { AuditReport, AuditRequest } from "../types/pedagogical";

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
//  1. auditPlanning  →  POST /audit
//     Sends a planning and receives a full AuditReport.
//
//  Usage with PlanningAgent output:
//    const report = await auditPlanning({
//      schedule:   planningResult.schedule,
//      group_name: "Group A",
//      planning_id: 1,
//    });
//
//  Usage with direct sessions:
//    const report = await auditPlanning({
//      sessions: [{ course: "Java", teacher: "Ahmed", ... }]
//    });
// =============================================================================

export async function auditPlanning(request: AuditRequest): Promise<AuditReport> {
  return apiFetch<AuditReport>("/audit", {
    method: "POST",
    body:   JSON.stringify(request),
  });
}

// =============================================================================
//  2. getPedagogicalRules  →  GET /audit/rules
//     Returns the active pedagogical_rules.json content.
//     Pass refresh=true to reload without restarting the server.
// =============================================================================

export async function getPedagogicalRules(refresh = false): Promise<{
  total_sections: number;
  rules:          Record<string, unknown>;
}> {
  const qs = refresh ? "?refresh=true" : "";
  return apiFetch(`/audit/rules${qs}`);
}

// =============================================================================
//  3. getAuditReport  →  GET /audit/report/{id}
//     Returns the cached AuditReport for a given planning_id.
// =============================================================================

export async function getAuditReport(planningId: number): Promise<AuditReport> {
  return apiFetch<AuditReport>(`/audit/report/${planningId}`);
}