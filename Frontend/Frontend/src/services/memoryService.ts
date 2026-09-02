/// <reference types="vite/client" />
// src/services/memoryService.ts

import type { Memory, MemorySummary, FeedbackRequest, MemoryType } from "../types/memory";

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

// GET /memories?user_id=...
export const getMemories = (userId: string, type?: MemoryType, limit = 50): Promise<{
  user_id: string; total: number; memories: Memory[];
}> => call(`/memories?user_id=${userId}${type ? `&memory_type=${type}` : ""}&limit=${limit}`);

// GET /memories/summary?user_id=...
export const getMemorySummary = (userId: string): Promise<MemorySummary> =>
  call(`/memories/summary?user_id=${userId}`);

// GET /memories/{id}
export const getMemory = (memoryId: number): Promise<Memory> =>
  call(`/memories/${memoryId}`);

// POST /memories/feedback
export const submitFeedback = (body: FeedbackRequest): Promise<{ success: boolean; memory_id: string }> =>
  call("/memories/feedback", { method: "POST", body: JSON.stringify(body) });

// DELETE /memories/{id}
export const deleteMemory = (memoryId: string): Promise<{ success: boolean }> =>
  call(`/memories/${memoryId}`, { method: "DELETE" });

// DELETE /memories?user_id=...
export const clearMemories = (userId: string): Promise<{ success: boolean; deleted_count: number }> =>
  call(`/memories?user_id=${userId}`, { method: "DELETE" });