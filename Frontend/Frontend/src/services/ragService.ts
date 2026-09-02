/// <reference types="vite/client" />
// src/services/ragService.ts

import type {
  RAGContextResponse, KnowledgeDocument,
  PlanningValidatedEvent, PlanningRejectedEvent, SessionMovedEvent,
} from "../types/rag";

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

// ── Context retrieval ─────────────────────────────────────────────────────────
export const getPlanningContext = (userId: string): Promise<RAGContextResponse> =>
  call("/rag/context/planning", { method: "POST", body: JSON.stringify({ user_id: userId }) });

export const getConstraintContext = (userId: string): Promise<RAGContextResponse> =>
  call("/rag/context/constraints", { method: "POST", body: JSON.stringify({ user_id: userId }) });

export const getPedagogicalContext = (userId: string): Promise<RAGContextResponse> =>
  call("/rag/context/pedagogical", { method: "POST", body: JSON.stringify({ user_id: userId }) });

// ── Events ────────────────────────────────────────────────────────────────────
export const notifyPlanningValidated = (e: PlanningValidatedEvent) =>
  call("/rag/events/planning-validated", { method: "POST", body: JSON.stringify(e) });

export const notifyPlanningRejected = (e: PlanningRejectedEvent) =>
  call("/rag/events/planning-rejected", { method: "POST", body: JSON.stringify(e) });

export const notifySessionMoved = (e: SessionMovedEvent) =>
  call("/rag/events/session-moved", { method: "POST", body: JSON.stringify(e) });

// ── Documents ─────────────────────────────────────────────────────────────────
export const listDocuments = (): Promise<{ total: number; documents: KnowledgeDocument[] }> =>
  call("/rag/documents");

export const ingestDocument = (body: {
  title: string; source?: string; document_type?: string; content: string;
}) => call("/rag/documents", { method: "POST", body: JSON.stringify(body) });

// ── Seed ──────────────────────────────────────────────────────────────────────
export const seedPedagogicalRules = (userId: string) =>
  call(`/rag/seed-rules?user_id=${userId}`, { method: "POST" });