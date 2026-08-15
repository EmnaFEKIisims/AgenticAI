// hooks/usePlanningValidation.ts

import { useState, useCallback } from "react";
import type { HITLStatus, ValidationResponse } from "../types/planningValidation";
import { validatePlanning, rejectPlanning } from "../services/planningManagementService";

interface UsePlanningValidationReturn {
  status:  HITLStatus;
  loading: boolean;
  error:   string | null;
  result:  ValidationResponse | null;
  validate:  (groupId: string, notes?: string) => Promise<void>;
  reject:    (groupId: string, reason?: string) => Promise<void>;
  reset:     () => void;
}

export function usePlanningValidation(): UsePlanningValidationReturn {
  const [status,  setStatus]  = useState<HITLStatus>("idle");
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);
  const [result,  setResult]  = useState<ValidationResponse | null>(null);

  const validate = useCallback(async (groupId: string, notes?: string) => {
    setLoading(true); setError(null);
    try {
      const r = await validatePlanning(groupId, notes);
      setResult(r);
      setStatus("validated");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Validation failed");
    } finally {
      setLoading(false);
    }
  }, []);

  const reject = useCallback(async (groupId: string, reason?: string) => {
    setLoading(true); setError(null);
    try {
      const r = await rejectPlanning(groupId, reason);
      setResult(r);
      setStatus("rejected");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Rejection failed");
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setStatus("idle"); setError(null); setResult(null); setLoading(false);
  }, []);

  return { status, loading, error, result, validate, reject, reset };
}