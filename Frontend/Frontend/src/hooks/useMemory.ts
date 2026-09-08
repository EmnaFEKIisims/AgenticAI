// src/hooks/useMemory.ts

import { useState, useEffect, useCallback } from "react";
import type { Memory, MemorySummary }        from "../types/memory";
import type { MemoryType }                   from "../types/rag";
import {
  getMemories, getMemorySummary,
  submitFeedback, deleteMemory, clearMemories,
} from "../services/memoryService";

const EMPTY_SUMMARY: MemorySummary = {
  user_id: "", total: 0,
  by_type: {
    user_preference: 0, decision_history: 0, planning_history: 0,
    conflict_correction: 0, user_feedback: 0, pedagogical_knowledge: 0,
  },
  recent: [],
};

interface UseMemoryReturn {
  memories:    Memory[];
  summary:     MemorySummary;
  filterType:  MemoryType | "all";
  isLoading:   boolean;
  error:       string | null;
  setFilterType: (v: MemoryType | "all") => void;
  refresh:     () => Promise<void>;
  onFeedback:  (feedback: string, context?: string, planningId?: string) => Promise<void>;
  onDelete:    (id: string) => Promise<void>;
  onClearAll:  () => Promise<void>;
}

export function useMemory(userId: string): UseMemoryReturn {
  const [memories,   setMemories]   = useState<Memory[]>([]);
  const [summary,    setSummary]    = useState<MemorySummary>(EMPTY_SUMMARY);
  const [filterType, setFilterType] = useState<MemoryType | "all">("all");
  const [isLoading,  setIsLoading]  = useState(false);
  const [error,      setError]      = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!userId) return;
    setIsLoading(true); setError(null);
    try {
      const [mems, sum] = await Promise.all([
        getMemories(userId, filterType === "all" ? undefined : filterType),
        getMemorySummary(userId),
      ]);
      setMemories(mems.memories);
      setSummary(sum);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load memories");
    } finally {
      setIsLoading(false);
    }
  }, [userId, filterType]);

  useEffect(() => { void refresh(); }, [refresh]);

  const onFeedback = useCallback(async (feedback: string, context = "", planningId = "") => {
    if (!userId || !feedback.trim()) return;
    await submitFeedback({ user_id: userId, feedback, context, planning_id: planningId });
    void refresh();
  }, [userId, refresh]);

  const onDelete = useCallback(async (id: string) => {
    await deleteMemory(id);
    setMemories(prev => prev.filter(m => m.id !== id));
    setSummary(prev => ({ ...prev, total: Math.max(0, prev.total - 1) }));
  }, []);

  const onClearAll = useCallback(async () => {
    if (!userId) return;
    await clearMemories(userId);
    setMemories([]); setSummary(EMPTY_SUMMARY);
  }, [userId]);

  return {
    memories, summary, filterType, isLoading, error,
    setFilterType, refresh, onFeedback, onDelete, onClearAll,
  };
}