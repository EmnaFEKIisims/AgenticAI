// hooks/useScheduleMove.ts
// Manages drag & drop state — TEMPORARY until admin confirms.

import { useState, useCallback } from "react";
import type { PendingMove, MoveResponse } from "../types/scheduleMove";
import type { ImpactResponse }            from "../types/impactAnalysis";
import { analyzeImpact, moveSession }     from "../services/planningManagementService";

interface UseScheduleMoveReturn {
  draggingSlotId:  number | null;
  pendingMove:     PendingMove | null;
  impact:          ImpactResponse | null;
  isAnalyzing:     boolean;
  isApplying:      boolean;
  error:           string | null;

  startDrag:  (slotId: number) => void;
  endDrag:    () => void;
  dropOn:     (pendingMove: PendingMove, planningGroupId?: string) => Promise<void>;
  confirmMove: (adminNote?: string) => Promise<MoveResponse | null>;
  cancelMove:  () => void;
}

export function useScheduleMove(): UseScheduleMoveReturn {
  const [draggingSlotId, setDraggingSlotId] = useState<number | null>(null);
  const [pendingMove,    setPendingMove]     = useState<PendingMove | null>(null);
  const [impact,         setImpact]          = useState<ImpactResponse | null>(null);
  const [isAnalyzing,    setIsAnalyzing]     = useState(false);
  const [isApplying,     setIsApplying]      = useState(false);
  const [error,          setError]           = useState<string | null>(null);

  const startDrag = useCallback((slotId: number) => {
    setDraggingSlotId(slotId);
  }, []);

  const endDrag = useCallback(() => {
    setDraggingSlotId(null);
  }, []);

  /** Called when admin drops a session onto a new cell. */
  const dropOn = useCallback(async (move: PendingMove, planningGroupId?: string) => {
    setPendingMove(move);
    setIsAnalyzing(true);
    setError(null);
    try {
      const result = await analyzeImpact(move.slot_id, {
        new_start_time:     move.target.start_time,
        new_end_time:       move.target.end_time,
        planning_group_id:  planningGroupId,
      });
      setImpact(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Impact analysis failed");
      setPendingMove(null);
    } finally {
      setIsAnalyzing(false);
    }
  }, []);

  /** Called when admin clicks "Confirm" in the ImpactPanel. */
  const confirmMove = useCallback(async (adminNote?: string): Promise<MoveResponse | null> => {
    if (!pendingMove) return null;
    setIsApplying(true); setError(null);
    try {
      const result = await moveSession(pendingMove.slot_id, {
        new_start_time: pendingMove.target.start_time,
        new_end_time:   pendingMove.target.end_time,
        admin_note:     adminNote,
      });
      setPendingMove(null);
      setImpact(null);
      return result;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Move failed");
      return null;
    } finally {
      setIsApplying(false);
    }
  }, [pendingMove]);

  /** Called when admin clicks "Cancel" in the ImpactPanel. */
  const cancelMove = useCallback(() => {
    setPendingMove(null);
    setImpact(null);
    setError(null);
  }, []);

  return {
    draggingSlotId, pendingMove, impact,
    isAnalyzing, isApplying, error,
    startDrag, endDrag, dropOn, confirmMove, cancelMove,
  };
}