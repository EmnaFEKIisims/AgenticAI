// hooks/usePedagogicalAudit.ts
// =============================
// Custom hook that owns:
//   - Audit state (idle / loading / success / error)
//   - API calls (via pedagogicalApi.ts)
//   - Derived helpers for the UI
//
// PedagogicalAuditPage calls this hook — zero API logic in the page.

import { useState, useCallback } from "react";
import type {
  PedagogicalAuditState,
  AuditReport,
  AuditRequest,
  CriterionResult,
} from "../types/pedagogical";
import { auditPlanning, getAuditReport } from "../services/pedagogicalService";

// =============================================================================
//  Initial state
// =============================================================================

const INITIAL: PedagogicalAuditState = {
  status: "idle",
  report: null,
  error:  null,
};

// =============================================================================
//  HOOK RETURN TYPE
// =============================================================================

interface UsePedagogicalAuditReturn {
  // State
  status:  PedagogicalAuditState["status"];
  report:  AuditReport | null;
  error:   string | null;

  // Derived
  isLoading:       boolean;
  hasReport:       boolean;
  isCompliant:     boolean;
  failedCriteria:  CriterionResult[];
  passedCriteria:  CriterionResult[];
  highViolations:  CriterionResult[];

  // Actions
  runAudit:    (request: AuditRequest) => Promise<void>;
  fetchReport: (planningId: number) => Promise<void>;
  reset:       () => void;
}

// =============================================================================
//  HOOK
// =============================================================================

export function usePedagogicalAudit(): UsePedagogicalAuditReturn {
  const [state, setState] = useState<PedagogicalAuditState>(INITIAL);

  // ── Derived values ──────────────────────────────────────────────────────────
  const isLoading      = state.status === "loading";
  const hasReport      = state.report !== null;
  const isCompliant    = state.report?.is_compliant ?? false;
  const failedCriteria = state.report?.criteria.filter(c => !c.passed)  ?? [];
  const passedCriteria = state.report?.criteria.filter(c =>  c.passed)  ?? [];
  const highViolations = failedCriteria.filter(c => c.severity === "high");

  // ── runAudit — POST /audit ──────────────────────────────────────────────────
  const runAudit = useCallback(async (request: AuditRequest) => {
    setState({ status: "loading", report: null, error: null });
    try {
      const report = await auditPlanning(request);
      setState({ status: "success", report, error: null });
    } catch (err) {
      setState({
        status: "error",
        report: null,
        error:  err instanceof Error ? err.message : "Audit failed",
      });
    }
  }, []);

  // ── fetchReport — GET /audit/report/{id} ────────────────────────────────────
  const fetchReport = useCallback(async (planningId: number) => {
    setState(s => ({ ...s, status: "loading", error: null }));
    try {
      const report = await getAuditReport(planningId);
      setState({ status: "success", report, error: null });
    } catch (err) {
      setState(s => ({
        ...s,
        status: "error",
        error:  err instanceof Error ? err.message : "Could not fetch report",
      }));
    }
  }, []);

  // ── reset ──────────────────────────────────────────────────────────────────
  const reset = useCallback(() => setState(INITIAL), []);

  return {
    status:  state.status,
    report:  state.report,
    error:   state.error,
    isLoading,
    hasReport,
    isCompliant,
    failedCriteria,
    passedCriteria,
    highViolations,
    runAudit,
    fetchReport,
    reset,
  };
}