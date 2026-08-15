// hooks/usePlanningRegeneration.ts

import { useState, useCallback } from "react";
import type { RegenerateResponse, SessionSlotOut } from "../types/planningRegeneration";
import { regeneratePlanning } from "../services/planningManagementService";

interface UsePlanningRegenerationReturn {
  regenerating:     boolean;
  error:            string | null;
  result:           RegenerateResponse | null;
  regenerate: (opts: {
    rejectedGroupId?: string;
    constraintsDict?: Record<string, unknown>;
    userConstraints?: string;
    attempt:          number;
  }) => Promise<RegenerateResponse | null>;
  reset: () => void;
}

export function usePlanningRegeneration(): UsePlanningRegenerationReturn {
  const [regenerating, setRegenerating] = useState(false);
  const [error,        setError]        = useState<string | null>(null);
  const [result,       setResult]       = useState<RegenerateResponse | null>(null);

  const regenerate = useCallback(async (opts: {
    rejectedGroupId?: string;
    constraintsDict?: Record<string, unknown>;
    userConstraints?: string;
    attempt:          number;
  }): Promise<RegenerateResponse | null> => {
    setRegenerating(true); setError(null);
    try {
      const r = await regeneratePlanning({
        rejected_group_id: opts.rejectedGroupId,
        constraints_dict:  opts.constraintsDict,
        user_constraints:  opts.userConstraints,
        attempt:           opts.attempt,
      });
      setResult(r);
      return r;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Regeneration failed");
      return null;
    } finally {
      setRegenerating(false);
    }
  }, []);

  const reset = useCallback(() => {
    setError(null); setResult(null); setRegenerating(false);
  }, []);

  return { regenerating, error, result, regenerate, reset };
}