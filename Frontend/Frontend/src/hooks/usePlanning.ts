// hooks/usePlanning.ts
// =====================
// Single custom hook that owns:
//   - All planning state
//   - All API calls (via planningService)
//   - All derived logic
//
// PlanningPage just calls usePlanning() and renders.
// Zero business logic lives in the component.
//
// ← FIXED: removed the dead/broken handleValidate (called validatePlanning()
//   with 0 arguments — TS2554 — superseded by usePlanningValidation.ts, which
//   PlanningPage actually uses).
// ← FIXED: handleRefresh no longer hardcodes validated:false. SessionSlot now
//   carries real status/is_validated (types/planning.ts), so we derive the
//   true validated state from the fetched schedule instead of assuming it's
//   always unvalidated on every refresh.

import { useState, useCallback, useRef } from "react";
import type {
  PlanningState,
  SessionSlot,
  Constraints,
} from "../types/planning";
import { normalizeDayLabel } from "../utils/planningHelpers";
import {
  runPlanning,
  getSchedule,
  exportCSV,
  getConstraints,
} from "../services/planningService";


// =============================================================================
//  State shape
// =============================================================================

interface UsePlanningReturn {
  // ── State ──────────────────────────────────────────────────────────────────
  state:           PlanningState;
  userInput:       string;
  dbConstraints:   Constraints | null;  // raw DB constraints (before merge)
  userConstraints: Constraints | null;  // constraints extracted by LLM from user text
  isExporting:     boolean;

  // ── Derived ────────────────────────────────────────────────────────────────
  hasSchedule:    boolean;
  canValidate:    boolean;
  canExport:      boolean;
  isLoading:      boolean;
  sessionsByDay:  Record<string, SessionSlot[]>;   // grouped for calendar view
  sessionsByCourse: Record<string, SessionSlot[]>; // grouped for course view

  // ── Actions ────────────────────────────────────────────────────────────────
  setUserInput:    (value: string) => void;
  handleRun:       () => Promise<void>;
  handleExport:    () => Promise<void>;
  handleRefresh:   () => Promise<void>;   // re-fetch last schedule from backend
  handleReset:     () => void;            // clear everything
  handleLoadConstraints: () => Promise<void>; // load DB constraints without running
  hydrateSchedule: (schedule: SessionSlot[], constraints?: Constraints | null) => void;
}


// =============================================================================
//  Initial state
// =============================================================================

const INITIAL_STATE: PlanningState = {
  status:      "idle",
  schedule:    [],
  constraints: null,
  error:       null,
  validated:   false,
};


// =============================================================================
//  Grouping helpers
// =============================================================================

function groupBy<T>(items: T[], key: keyof T): Record<string, T[]> {
  return items.reduce((acc, item) => {
    const k = String(item[key]);
    if (!acc[k]) acc[k] = [];
    acc[k].push(item);
    return acc;
  }, {} as Record<string, T[]>);
}

/** True only if every slot in the schedule is validated. Empty schedule → false. */
function deriveValidated(schedule: SessionSlot[]): boolean {
  return schedule.length > 0 && schedule.every((s) => s.status === "validated");
}


// =============================================================================
//  Hook
// =============================================================================

export function usePlanning(): UsePlanningReturn {

  const [state,           setState]           = useState<PlanningState>(INITIAL_STATE);
  const [userInput,       setUserInput]       = useState<string>("");
  const [dbConstraints,   setDbConstraints]   = useState<Constraints | null>(null);
  const [userConstraints, setUserConstraints] = useState<Constraints | null>(null);
  const [isExporting,     setIsExporting]     = useState<boolean>(false);

  // Abort controller — cancels in-flight requests if user re-runs
  const abortRef = useRef<AbortController | null>(null);


  // ── Derived values ──────────────────────────────────────────────────────────

  const hasSchedule = state.schedule.length > 0;
  const canValidate = state.status === "success" && hasSchedule && !state.validated;
  const canExport   = hasSchedule && (state.status === "success" || state.status === "validated");
  const isLoading   = state.status === "loading";

  // Group sessions by day  → used by a calendar/day-view component
  const sessionsByDay: Record<string, SessionSlot[]> =
    hasSchedule
      ? state.schedule.reduce((acc, session) => {
          const day = normalizeDayLabel(session.suggested_day);
          if (!acc[day]) acc[day] = [];
          acc[day].push(session);
          return acc;
        }, {} as Record<string, SessionSlot[]>)
      : {};

  // Group sessions by course → used by a course-breakdown component
  const sessionsByCourse: Record<string, SessionSlot[]> =
    hasSchedule ? groupBy(state.schedule, "course_title") : {};


  // ── handleRun ───────────────────────────────────────────────────────────────
  // Sends user constraints (if any) to the agent, stores full response.

  const handleRun = useCallback(async () => {
    // Cancel any previous request
    if (abortRef.current) abortRef.current.abort();
    abortRef.current = new AbortController();

    setState({
      status:      "loading",
      schedule:    [],
      constraints: null,
      error:       null,
      validated:   false,
    });
    setDbConstraints(null);
    setUserConstraints(null);

    try {
      const res = await runPlanning(userInput.trim() || undefined);

      setDbConstraints(res.db_constraints);
      setUserConstraints(
        userInput.trim() ? res.user_constraints : null
      );

      setState({
        status:      "success",
        schedule:    res.schedule,
        constraints: res.final_constraints,
        error:       null,
        validated:   false,   // a fresh generation is always unvalidated
      });
    } catch (err) {
      if ((err as Error).name === "AbortError") return; // user cancelled
      setState((s) => ({
        ...s,
        status: "error",
        error:  err instanceof Error ? err.message : "Unexpected error",
      }));
    }
  }, [userInput]);


  // ── handleExport ────────────────────────────────────────────────────────────
  // Triggers CSV download via the service (creates a temporary <a> element).

  const handleExport = useCallback(async () => {
    if (!canExport) return;
    setIsExporting(true);
    try {
      await exportCSV();
    } catch (err) {
      setState((s) => ({
        ...s,
        status: "error",
        error:  err instanceof Error ? err.message : "Export failed",
      }));
    } finally {
      setIsExporting(false);
    }
  }, [canExport]);


  // ── handleRefresh ───────────────────────────────────────────────────────────
  // Re-fetches the last schedule stored in backend memory
  // (useful after page reload/remount, without re-running the agent).

  const handleRefresh = useCallback(async () => {
    setState((s) => ({ ...s, status: "loading", error: null }));
    try {
      const schedule = await getSchedule();

      // ← FIXED: derive the real validated state from the fetched slots
      //   instead of hardcoding false. SessionSlot now carries `status`,
      //   so we can tell truth from the backend rather than assuming
      //   every refresh means "nothing validated yet".
      const validated = deriveValidated(schedule);

      setState((s) => ({
        ...s,
        status:    validated ? "validated" : "success",
        schedule,
        validated,
      }));
    } catch (err) {
      const message = err instanceof Error ? err.message : "Could not fetch schedule";

      // Opening planning before any schedule exists should show the empty state, not an error.
      if (/no\s+schedule\s+found|not\s+found|http\s*404/i.test(message)) {
        setState((s) => ({
          ...s,
          status: "idle",
          schedule: [],
          error: null,
          validated: false,
        }));
        return;
      }

      setState((s) => ({
        ...s,
        status: "error",
        error:  message,
      }));
    }
  }, []);


  // ── handleReset ─────────────────────────────────────────────────────────────
  // Clears everything back to the initial idle state.

  const handleReset = useCallback(() => {
    if (abortRef.current) abortRef.current.abort();
    setState(INITIAL_STATE);
    setUserInput("");
    setDbConstraints(null);
    setUserConstraints(null);
  }, []);


  // ── handleLoadConstraints ───────────────────────────────────────────────────
  // Fetches DB constraints without running the agent.
  // Used to preview what constraints are active before running.

  const handleLoadConstraints = useCallback(async () => {
    try {
      const res = await getConstraints();
      setDbConstraints(res.constraints);
      setState((s) => ({
        ...s,
        constraints: res.constraints,
      }));
    } catch (err) {
      setState((s) => ({
        ...s,
        status: "error",
        error:  err instanceof Error ? err.message : "Could not load constraints",
      }));
    }
  }, []);

  const hydrateSchedule = useCallback((schedule: SessionSlot[], constraints?: Constraints | null) => {
    const validated = deriveValidated(schedule);
    setState((s) => ({
      ...s,
      status: validated ? "validated" : "success",
      schedule,
      constraints: constraints ?? s.constraints,
      error: null,
      validated,
    }));
  }, []);


  // ── Return ──────────────────────────────────────────────────────────────────

  return {
    // State
    state,
    userInput,
    dbConstraints,
    userConstraints,
    isExporting,

    // Derived
    hasSchedule,
    canValidate,
    canExport,
    isLoading,
    sessionsByDay,
    sessionsByCourse,

    // Actions
    setUserInput,
    handleRun,
    handleExport,
    handleRefresh,
    handleReset,
    handleLoadConstraints,
    hydrateSchedule,
  };
}