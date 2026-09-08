/// <reference types="vite/client" />
// src/services/memoryService.ts
// Updated: uses central apiFetch → X-User-ID auto-injected
// Note: user_id is ALSO passed in query params for memory endpoints
// (backend reads from query, not just header — both are set for safety)

import { apiGet, apiPost, apiDelete, apiFetch } from "./api";

import type { Memory, MemorySummary, FeedbackRequest } from "../types/memory";
import type { MemoryType } from "../types/rag";

// GET /memories?user_id=...
export const getMemories = (
  userId: string,
  type?:  MemoryType,
  limit = 50,
): Promise<{ user_id: string; total: number; memories: Memory[] }> =>
  apiGet(`/memories?user_id=${userId}${type ? `&memory_type=${type}` : ""}&limit=${limit}`);

// GET /memories/summary?user_id=...
export const getMemorySummary = (userId: string): Promise<MemorySummary> =>
  apiGet(`/memories/summary?user_id=${userId}`);

// GET /memories/{id}
export const getMemory = (memoryId: number): Promise<Memory> =>
  apiGet(`/memories/${memoryId}`);

// POST /memories/feedback
export const submitFeedback = (
  body: FeedbackRequest,
): Promise<{ success: boolean; memory_id: string }> =>
  apiPost("/memories/feedback", body);

// DELETE /memories/{id}
export const deleteMemory = (memoryId: string): Promise<{ success: boolean }> =>
  apiDelete(`/memories/${memoryId}`);

// DELETE /memories?user_id=...
export const clearMemories = (
  userId: string,
): Promise<{ success: boolean; deleted_count: number }> =>
  apiDelete(`/memories?user_id=${userId}`);