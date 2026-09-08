/// <reference types="vite/client" />
// src/services/ragService.ts
// Updated: uses central apiFetch → X-User-ID auto-injected
// Note: user_id is also passed in request body for RAG endpoints

import { apiGet, apiPost } from "./api";

import type {
  RAGContextResponse,
  KnowledgeDocument,
  PlanningValidatedEvent,
  PlanningRejectedEvent,
  SessionMovedEvent,
} from "../types/rag";

// ── Context retrieval ─────────────────────────────────────────────────────────

export const getPlanningContext = (userId: string): Promise<RAGContextResponse> =>
  apiPost("/rag/context/planning", { user_id: userId });

export const getConstraintContext = (userId: string): Promise<RAGContextResponse> =>
  apiPost("/rag/context/constraints", { user_id: userId });

export const getPedagogicalContext = (userId: string): Promise<RAGContextResponse> =>
  apiPost("/rag/context/pedagogical", { user_id: userId });

// ── Events ────────────────────────────────────────────────────────────────────

export const notifyPlanningValidated = (e: PlanningValidatedEvent): Promise<unknown> =>
  apiPost("/rag/events/planning-validated", e);

export const notifyPlanningRejected = (e: PlanningRejectedEvent): Promise<unknown> =>
  apiPost("/rag/events/planning-rejected", e);

export const notifySessionMoved = (e: SessionMovedEvent): Promise<unknown> =>
  apiPost("/rag/events/session-moved", e);

// ── Documents ─────────────────────────────────────────────────────────────────

export const listDocuments = (): Promise<{ total: number; documents: KnowledgeDocument[] }> =>
  apiGet("/rag/documents");

export const ingestDocument = (body: {
  title: string; source?: string; document_type?: string; content: string;
}): Promise<unknown> => apiPost("/rag/documents", body);

// ── Seed ──────────────────────────────────────────────────────────────────────

export const seedPedagogicalRules = (userId: string): Promise<unknown> =>
  apiPost(`/rag/seed-rules?user_id=${userId}`);