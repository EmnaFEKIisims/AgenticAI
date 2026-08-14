// services/anomalyService.ts
// ============================
// All API calls for the Anomaly Agent.
// Matches exactly api/AnomalyRouter.py endpoints.

import type {
  Anomaly,
  AnalyzeRequest,
  AnalyzeResponse,
  StatusUpdate,
  SuggestionsResponse,
  ImpactRequest,
  ImpactResponse,
} from "../types/anomaly";

const BASE_URL = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "")
              ?? "http://localhost:8000";

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
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
//  1. POST /anomalies/analyze/{planning_id}
//     Run full anomaly detection on a planning
// =============================================================================

export async function analyzeAnomalies(
  planningId: number,
  body: AnalyzeRequest,
): Promise<AnalyzeResponse> {
  return apiFetch<AnalyzeResponse>(`/anomalies/analyze/${planningId}`, {
    method: "POST",
    body:   JSON.stringify(body),
  });
}



export async function getAllAnomalies(): Promise<Anomaly[]> {
  return apiFetch<Anomaly[]>("/anomalies");
}

// =============================================================================
//  2. GET /anomalies/planning/{planning_id}
//     Get all anomalies for a planning
// =============================================================================

export async function getAnomaliesByPlanning(planningId: number): Promise<Anomaly[]> {
  return apiFetch<Anomaly[]>(`/anomalies/planning/${planningId}`);
}

// =============================================================================
//  3. GET /anomalies/{anomaly_id}
//     Get a single anomaly
// =============================================================================

export async function getAnomaly(anomalyId: number): Promise<Anomaly> {
  return apiFetch<Anomaly>(`/anomalies/${anomalyId}`);
}

// =============================================================================
//  4. PATCH /anomalies/{anomaly_id}/status
//     Update anomaly status (HITL)
// =============================================================================

export async function updateAnomalyStatus(
  anomalyId: number,
  status: StatusUpdate["status"],
): Promise<Anomaly> {
  return apiFetch<Anomaly>(`/anomalies/${anomalyId}/status`, {
    method: "PATCH",
    body:   JSON.stringify({ status }),
  });
}

// =============================================================================
//  5. POST /anomalies/{anomaly_id}/suggestions
//     Get resolution proposals
// =============================================================================

export async function getAnomalySuggestions(
  anomalyId: number,
  schedule:  Record<string, unknown>[],
): Promise<SuggestionsResponse> {
  return apiFetch<SuggestionsResponse>(`/anomalies/${anomalyId}/suggestions`, {
    method: "POST",
    body:   JSON.stringify({ schedule }),
  });
}

// =============================================================================
//  6. POST /anomalies/impact-analysis
//     Analyze cascading impact of moving a session
// =============================================================================

export async function analyzeImpact(body: ImpactRequest): Promise<ImpactResponse> {
  return apiFetch<ImpactResponse>("/anomalies/impact-analysis", {
    method: "POST",
    body:   JSON.stringify(body),
  });
}