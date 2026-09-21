// hooks/usePedagogicalAudit.ts
// =============================
// Custom hook that owns:
//   - Audit state (idle / loading / success / error)
//   - API calls (via pedagogicalApi.ts)
//   - Derived helpers for the UI
//
// PedagogicalAuditPage calls this hook — zero API logic in the page.

import { useState, useCallback, useRef } from "react";
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
  hydrateReport: (report: AuditReport) => void;
  reset:       () => void;
}

// =============================================================================
//  HOOK
// =============================================================================

export function usePedagogicalAudit(): UsePedagogicalAuditReturn {
  const [state, setState] = useState<PedagogicalAuditState>(INITIAL);

  // ← ADDED: monotonically increasing id for the "current" in-flight
  //   request. Confirmed root cause of the 66 → 63.4 flip-flop reported
  //   in production: two runAudit() calls fired close together (one with
  //   fresh schedule data, one with stale data), and whichever response
  //   came back LAST simply overwrote `state` — even when it was the
  //   stale one. This ref lets each in-flight call check, right before
  //   writing state, whether it is still the most recent call that was
  //   started; a call that's been superseded by a newer one silently
  //   drops its result instead of clobbering the fresher state.
  const requestIdRef = useRef(0);

  // ── Derived values ──────────────────────────────────────────────────────────
  const isLoading      = state.status === "loading";
  const hasReport      = state.report !== null;
  const isCompliant    = state.report?.is_compliant ?? false;
  const failedCriteria = state.report?.criteria.filter(c => !c.passed)  ?? [];
  const passedCriteria = state.report?.criteria.filter(c =>  c.passed)  ?? [];
  const highViolations = failedCriteria.filter(c => c.severity === "high");

  // ── runAudit — POST /audit ──────────────────────────────────────────────────
  const runAudit = useCallback(async (request: AuditRequest) => {
    const myRequestId = ++requestIdRef.current;
    setState({ status: "loading", report: null, error: null });
    try {
      const report = await auditPlanning(request);
      // ← A newer runAudit()/fetchReport() call started while this one was
      //   in flight — that call owns the state now, so this stale result
      //   is discarded instead of overwriting whatever it produced.
      if (myRequestId !== requestIdRef.current) return;
      setState({ status: "success", report, error: null });
    } catch (err) {
      if (myRequestId !== requestIdRef.current) return;
      setState({
        status: "error",
        report: null,
        error:  err instanceof Error ? err.message : "Audit failed",
      });
    }
  }, []);

  // ── fetchReport — GET /audit/report/{id} ────────────────────────────────────
  const fetchReport = useCallback(async (planningId: number) => {
    const myRequestId = ++requestIdRef.current;
    setState(s => ({ ...s, status: "loading", error: null }));
    try {
      const report = await getAuditReport(planningId);
      if (myRequestId !== requestIdRef.current) return;
      setState({ status: "success", report, error: null });
    } catch (err) {
      if (myRequestId !== requestIdRef.current) return;
      setState(s => ({
        ...s,
        status: "error",
        error:  err instanceof Error ? err.message : "Could not fetch report",
      }));
    }
  }, []);

  const hydrateReport = useCallback((report: AuditReport) => {
    // Hydrating from cache also "claims" the request slot, so a slow
    // in-flight runAudit from before this hydration can't later overwrite
    // it with a stale result either.
    requestIdRef.current += 1;
    setState({ status: "success", report, error: null });
  }, []);

  // ── reset ──────────────────────────────────────────────────────────────────
  const reset = useCallback(() => {
    requestIdRef.current += 1;
    setState(INITIAL);
  }, []);

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
    hydrateReport,
    reset,
  };
}