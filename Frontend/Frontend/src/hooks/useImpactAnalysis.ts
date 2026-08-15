// hooks/useImpactAnalysis.ts
// Standalone hook for on-demand impact analysis (without drag & drop context).

import { useState, useCallback } from "react";
import type { ImpactResponse }   from "../types/impactAnalysis";
import { analyzeImpact }         from "../services/planningManagementService";

interface UseImpactAnalysisReturn {
  impact:     ImpactResponse | null;
  loading:    boolean;
  error:      string | null;
  analyze:    (slotId: number, newStart: string, newEnd: string, groupId?: string) => Promise<void>;
  clearImpact: () => void;
}

export function useImpactAnalysis(): UseImpactAnalysisReturn {
  const [impact,  setImpact]  = useState<ImpactResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  const analyze = useCallback(async (
    slotId: number, newStart: string, newEnd: string, groupId?: string
  ) => {
    setLoading(true); setError(null);
    try {
      const r = await analyzeImpact(slotId, {
        new_start_time:    newStart,
        new_end_time:      newEnd,
        planning_group_id: groupId,
      });
      setImpact(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  }, []);

  const clearImpact = useCallback(() => {
    setImpact(null); setError(null);
  }, []);

  return { impact, loading, error, analyze, clearImpact };
}