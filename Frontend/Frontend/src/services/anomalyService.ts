// services/anomalyService.ts
// ============================
// FIXED to match the EXACT export names your hooks/useAnomalies.ts imports
// (getAllAnomalies, getAnomaliesByPlanning, updateAnomalyStatus,
// getAnomalySuggestions) — the previous pass renamed these and broke the
// build. Root fix is unchanged: everything goes through apiGet/apiPost/
// apiPatch from ./api, which sends X-User-ID on every call.

import { apiGet, apiPost, apiPatch } from "./api";
import type {
  Anomaly,
  AnalyzeRequest,
  AnalyzeResponse,
  SuggestionsResponse,
  ImpactRequest,
  ImpactResponse,
} from "../types/anomaly";

export async function getAllAnomalies(): Promise<Anomaly[]> {
  return apiGet<Anomaly[]>("/anomalies/");
}

export async function getAnomaliesByPlanning(planningId: number): Promise<Anomaly[]> {
  return apiGet<Anomaly[]>(`/anomalies/planning/${planningId}`);
}

export async function getAnomaly(anomalyId: number): Promise<Anomaly> {
  return apiGet<Anomaly>(`/anomalies/${anomalyId}`);
}

export async function updateAnomalyStatus(
  anomalyId: number,
  status: "acknowledged" | "resolved" | "ignored",
): Promise<Anomaly> {
  return apiPatch<Anomaly>(`/anomalies/${anomalyId}/status`, { status });
}

export async function getAnomalySuggestions(
  anomalyId: number,
  schedule: Record<string, unknown>[],
): Promise<SuggestionsResponse> {
  return apiPost<SuggestionsResponse>(`/anomalies/${anomalyId}/suggestions`, { schedule });
}

export async function analyzePlanning(
  planningId: number,
  payload: AnalyzeRequest,
): Promise<AnalyzeResponse> {
  return apiPost<AnalyzeResponse>(`/anomalies/analyze/${planningId}`, payload);
}

export async function getImpactAnalysis(payload: ImpactRequest): Promise<ImpactResponse> {
  return apiPost<ImpactResponse>("/anomalies/impact-analysis", payload);
}