import { useEffect, useState, useCallback, useMemo } from "react";
import { useLocation, useNavigate }         from "react-router-dom";
import { usePlanning }                      from "../hooks/usePlanning";

// ── Existing view components ─────────────────────────────────────────────────
import PlanningTable        from "../components/planning/PlanningTable";
import GroupedPlanningView  from "../components/planning/GroupedPlanningView";

// ── NEW: HITL + DnD components ───────────────────────────────────────────────
import ValidationActions    from "../components/planning/ValidationActions";
import ValidationDialog     from "../components/planning/ValidationDialog";
import RegenerationDialog   from "../components/planning/RegenerationDialog";
import ScheduleGrid         from "../components/planning/ScheduleGrid";
import ImpactPanel          from "../components/planning/ImpactPanel";

// ── NEW: hooks ───────────────────────────────────────────────────────────────
import { usePlanningValidation }   from "../hooks/usePlanningValidation";
import { usePlanningRegeneration } from "../hooks/usePlanningRegeneration";
import { useScheduleMove }         from "../hooks/useScheduleMove";

// ── Types ────────────────────────────────────────────────────────────────────
import type { PendingMove }    from "../types/scheduleMove";
import type { SessionSlotOut } from "../types/planningRegeneration";
import type { SessionSlot, SlotStatus } from "../types/planning";
import type { HITLStatus }     from "../types/planningValidation";
import NotificationBell        from "../components/notifications/NotificationBell";

import {
  Check, CircleAlert, Download, GraduationCap,
  LayoutGrid, Loader2, Pin, RefreshCw, Sparkles, Users,
  MoreHorizontal, Search, TrendingUp, ClipboardCheck,
  Move, XCircle, Settings2,
  UserRound,
} from "lucide-react";

type PlanningViewMode = "global" | "group" | "trainer" | "dnd";

// ── ADDED: base URL used elsewhere in the app's services. If your services
//   use an axios instance with its own baseURL, replace this fetch call with
//   a proper `getLastState()` export from planningService.ts instead — this
//   inline version exists only so PlanningPage doesn't need that file to be
//   handed over to build the fix. ───────────────────────────────────────────
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

async function fetchLastState(): Promise<{
  has_planning: boolean;
  planning_group_id: string;
  hitl_status: "idle" | "pending" | "validated" | "rejected";
} | null> {
  try {
    const res = await fetch(`${API_BASE}/planning/last-state`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export default function PlanningPage() {

  // ── Existing state ──────────────────────────────────────────────────────────
  const [mode,          setMode]          = useState<PlanningViewMode>("global");
  const [showReasoning, setShowReasoning] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  // ── NEW state ────────────────────────────────────────────────────────────────
  const [planningGroupId, setPlanningGroupId] = useState("");
  const [hitlStatus,      setHitlStatus]      = useState<HITLStatus>("idle");
  const [attempt,         setAttempt]         = useState(1);
  const [currentWeek,     setCurrentWeek]     = useState(1);
  const [localSchedule,   setLocalSchedule]   = useState<SessionSlotOut[]>([]);
  const [dialog,          setDialog]          = useState<"none"|"reject"|"regenerate">("none");
  const [searchQuery,     setSearchQuery]     = useState("");
  const [isSearchOpen,    setIsSearchOpen]    = useState(false);
  // ← ADDED: surfaces the case where Validate/Reject can't reach the backend
  //   because planningGroupId is empty, instead of silently pretending success.
  const [hitlError,       setHitlError]       = useState<string | null>(null);

  // ── Existing hook ────────────────────────────────────────────────────────────
  const {
    state, isExporting, hasSchedule,
    canExport, isLoading, sessionsByCourse,
    handleExport, handleRefresh, handleReset, hydrateSchedule,
  } = usePlanning();

  // ── NEW hooks ────────────────────────────────────────────────────────────────
  const validation   = usePlanningValidation();
  const regeneration = usePlanningRegeneration();
  const move         = useScheduleMove();

  // ── Sync localSchedule ───────────────────────────────────────────────────────
  // ← FIXED: previously this hardcoded start_time/end_time to "" and
  //   status/is_validated to "draft"/false on every run — discarding real
  //   move/validation data any time state.schedule changed reference,
  //   including right after a successful move (hydrateSchedule call).
  //   SessionSlot now carries the real fields (types/planning.ts), so we
  //   use them directly instead of hardcoding, and we derive hitlStatus
  //   from the real per-slot status instead of always forcing "pending".
  useEffect(() => {
    if (state.schedule?.length) {
      const mapped: SessionSlotOut[] = state.schedule.map((s: SessionSlot) => ({
        id: s.id,
        // ← ADDED: every session now carries its own group id from the
        //   backend, so the frontend can always derive the current
        //   planning_group_id straight from the loaded schedule instead of
        //   trusting navigation state (which was found to silently drop
        //   this field, and — more importantly — to go stale on browser
        //   "back" navigation, see the hydrate effect below).
        planning_group_id: s.planning_group_id,
        session_number: s.session_number,
        course_id: s.course_id,
        course_title: s.course_title,
        trainer_id: s.trainer_id,
        trainer_name: s.trainer_name,
        room_id: s.room_id,
        room_name: s.room_name,
        group_name: s.group_name,
        learner_group_id: s.group_id ?? 0,
        suggested_day: s.suggested_day,
        suggested_time: s.suggested_time,
        start_time: s.start_time ?? "",
        end_time: s.end_time ?? "",
        status: s.status ?? "draft",
        is_validated: s.is_validated ?? false,
        quality_score: s.quality_score ?? 0,
        pedagogical_audit_score: s.pedagogical_audit_score ?? 0,
        reasoning: s.reasoning,
      }));
      setLocalSchedule(mapped);

      // ← ADDED: derive planningGroupId directly from the schedule's own
      //   data (every session carries planning_group_id from the backend)
      //   instead of relying on navigation state or an ephemeral cache.
      const groupIdFromSchedule = mapped.find(s => s.planning_group_id)?.planning_group_id;
      if (groupIdFromSchedule && groupIdFromSchedule !== planningGroupId) {
        setPlanningGroupId(groupIdFromSchedule);
      }

      // Derive hitlStatus from real backend truth instead of blindly
      // forcing "pending" whenever a schedule shows up.
      const allValidated = mapped.every(s => s.status === "validated");
      const allRejected  = mapped.length > 0 && mapped.every(s => s.status === "rejected");
      if (allValidated) {
        setHitlStatus("validated");
      } else if (allRejected) {
        setHitlStatus("rejected");
      } else if (hitlStatus === "idle") {
        setHitlStatus("pending");
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.schedule]);

  // ── Hydrate on mount ─────────────────────────────────────────────────────────
  // ← FIXED (root cause of "à chaque fois je valide, au retour ça revient
  //   à l'état initial" — confirmed even AFTER the DB-sourced
  //   PlanningRouter.py fix): this used to take an early `return` whenever
  //   `location.state.preloadedSchedule` was present, and NEVER call the
  //   backend in that case.
  //
  //   The bug: `location.state` is frozen on the history entry at the
  //   moment it was pushed. When you land on /planning via
  //   `navigate("/planning", { state: {...} })` from ConstraintPage, that
  //   state is the freshly-generated DRAFT schedule. If you later validate
  //   (pure React state change — it does NOT re-push a new history entry)
  //   and then return here via a generic "back" button (`navigate(-1)` /
  //   browser back), React Router replays that SAME, ORIGINAL history
  //   entry — with its ORIGINAL, now-stale `location.state`. The old code
  //   trusted that stale draft data and never asked the backend, so the
  //   validated/moved state you'd just saved to the DB was never even
  //   requested, let alone shown.
  //
  //   Fix: `location.state.preloadedSchedule`, when present, is used only
  //   for an instant optimistic paint (avoids a blank/loading flash on
  //   first arrival from ConstraintPage). We then ALWAYS reconcile with
  //   the backend's real, DB-sourced state via /last-state + a full
  //   /schedule refresh — on every mount, regardless of whether nav state
  //   was present. The DB is now the only thing that gets the final word.
  useEffect(() => {
    const navState = location.state as {
      preloadedSchedule?:    unknown;
      preloadedConstraints?: unknown;
      planningGroupId?:      string;
    } | null;

    if (navState?.planningGroupId) setPlanningGroupId(navState.planningGroupId);

    // Optimistic instant paint only — NOT treated as authoritative anymore.
    if (Array.isArray(navState?.preloadedSchedule) && navState.preloadedSchedule.length > 0) {
      const pre = navState.preloadedSchedule as unknown[];
      const asSessionSlots: SessionSlot[] = pre.map((p: any) => ({
        id: p.id,
        planning_group_id: p.planning_group_id,
        session_number: p.session_number,
        course_id: p.course_id,
        course_title: p.course_title,
        trainer_id: p.trainer_id,
        trainer_name: p.trainer_name,
        room_id: p.room_id,
        room_name: p.room_name,
        group_id: p.group_id ?? p.learner_group_id ?? 0,
        group_name: p.group_name,
        suggested_day: p.suggested_day,
        suggested_time: p.suggested_time,
        reasoning: p.reasoning ?? "",
        start_time: p.start_time ?? "",
        end_time: p.end_time ?? "",
        status: p.status ?? "draft",
        is_validated: p.is_validated ?? false,
        quality_score: p.quality_score ?? 0,
        pedagogical_audit_score: p.pedagogical_audit_score ?? 0,
      }));

      hydrateSchedule(asSessionSlots, (navState.preloadedConstraints as typeof state.constraints) ?? null);
      // ← No `return` here anymore — we fall through and still reconcile
      //   with the backend below, which is exactly what was missing.
    }

    // ← ALWAYS re-derive the current planning + its real HITL status from
    //   the backend (now DB-sourced, see PlanningRouter.py), whether or
    //   not navigation state was present. This is what makes the page
    //   correct on every return path: a fresh nav from ConstraintPage, a
    //   remount after /pedagogical-audit, or a browser "back" that replays
    //   stale history state.
    (async () => {
      const last = await fetchLastState();
      if (last?.has_planning) {
        setPlanningGroupId(last.planning_group_id);
        if (last.hitl_status === "validated") setHitlStatus("validated");
        else if (last.hitl_status === "rejected") setHitlStatus("rejected");
        else setHitlStatus("pending");
      }
      void handleRefresh();   // pulls the full, authoritative schedule (GET /planning/schedule)
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);   // ← run once only, on every mount of this page

  // ── Stats ────────────────────────────────────────────────────────────────────
  const totalSessions = state.schedule.length;
  const totalDays     = new Set(state.schedule.map((session) => session.suggested_day)).size;
  const totalCourses  = Object.keys(sessionsByCourse).length;
  const totalWeeks    = localSchedule.length > 0
    ? Math.max(...localSchedule.map(s => parseInt(s.suggested_day?.match(/Week\s+(\d+)/i)?.[1] ?? "1")))
    : 1;

  const filteredSchedule = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    if (!query) return state.schedule;

    return state.schedule.filter((session) => [
      session.course_title,
      session.trainer_name,
      session.room_name,
      session.group_name,
      session.suggested_day,
      session.suggested_time,
    ].some((value) => String(value ?? "").toLowerCase().includes(query)));
  }, [searchQuery, state.schedule]);

  // =============================================================================
  //  HITL Handlers — use planningManagementService (correct endpoints)
  // =============================================================================

  // ← FIXED: this used to ONLY flip the local hitlStatus flag, leaving the
  //   actual schedule data (localSchedule / state.schedule) still marked
  //   "draft". That stale "draft" data is exactly what gets forwarded as
  //   navigation state to /pedagogical-audit — and (see the mount effect
  //   above) navigation state can never be trusted as authoritative again
  //   anyway, but keeping it accurate here still avoids a visible flash of
  //   wrong data before the backend reconciliation above completes.
  const handleValidate = useCallback(async () => {
    setHitlError(null);
    let groupId = planningGroupId;

    if (!groupId) {
      const last = await fetchLastState();
      groupId = last?.planning_group_id ?? "";
      if (groupId) setPlanningGroupId(groupId);
    }

    if (!groupId) {
      setHitlError("Cannot validate: no planning group found. Try refreshing the page.");
      return;   // ← do NOT flip hitlStatus — nothing was actually saved
    }

    await validation.validate(groupId);
    setHitlStatus("validated");

    setLocalSchedule(prev => prev.map(s => ({ ...s, status: "validated", is_validated: true })));
    const validatedForState: SessionSlot[] = state.schedule.map(s => ({
      ...s,
      status: "validated" as SlotStatus,
      is_validated: true,
    }));
    hydrateSchedule(validatedForState, state.constraints);
  }, [planningGroupId, validation, state.schedule, state.constraints, hydrateSchedule]);

  const handleRejectConfirm = useCallback(async (reason: string) => {
    setHitlError(null);
    let groupId = planningGroupId;

    if (!groupId) {
      const last = await fetchLastState();
      groupId = last?.planning_group_id ?? "";
      if (groupId) setPlanningGroupId(groupId);
    }

    if (!groupId) {
      setHitlError("Cannot reject: no planning group found. Try refreshing the page.");
      setDialog("none");
      return;
    }

    await validation.reject(groupId, reason);
    setHitlStatus("rejected");
    setLocalSchedule([]);
    setDialog("none");
    handleReset();
  }, [planningGroupId, validation, handleReset]);

  // =============================================================================
  //  Regeneration
  // =============================================================================

  const handleRegenerate = useCallback(async (userConstraints: string) => {
    const nextAttempt = attempt + 1;
    const res = await regeneration.regenerate({
      rejectedGroupId: planningGroupId,
      userConstraints: userConstraints || undefined,
      attempt:         nextAttempt,
    });
    if (res) {
      setLocalSchedule(res.schedule ?? []);
      setPlanningGroupId(res.planning_group_id);
      setHitlStatus("pending");
      setAttempt(nextAttempt);
      setCurrentWeek(1);
      // Convert SessionSlotOut[] -> SessionSlot[] for hydrateSchedule
      const fromOut: SessionSlot[] = (res.schedule ?? []).map((p: any) => ({
        id: p.id,
        planning_group_id: p.planning_group_id ?? res.planning_group_id,
        session_number: p.session_number,
        course_id: p.course_id,
        course_title: p.course_title,
        trainer_id: p.trainer_id,
        trainer_name: p.trainer_name,
        room_id: p.room_id,
        room_name: p.room_name,
        group_id: p.group_id ?? p.learner_group_id ?? 0,
        group_name: p.group_name,
        suggested_day: p.suggested_day,
        suggested_time: p.suggested_time,
        reasoning: p.reasoning ?? "",
        start_time: p.start_time ?? "",
        end_time: p.end_time ?? "",
        status: p.status ?? "draft",
        is_validated: p.is_validated ?? false,
        quality_score: p.quality_score ?? 0,
        pedagogical_audit_score: p.pedagogical_audit_score ?? 0,
      }));
      hydrateSchedule(fromOut, null);
    }
    setDialog("none");
  }, [attempt, planningGroupId, regeneration, hydrateSchedule]);

  // =============================================================================
  //  Drag & Drop
  // =============================================================================

  const handleDragStart = useCallback((e: React.DragEvent, session: SessionSlotOut) => {
    e.dataTransfer.effectAllowed = "move";
    move.startDrag(session.id ?? session.session_number);
  }, [move]);

  const handleDrop = useCallback(async (pendingMove: PendingMove) => {
    await move.dropOn(pendingMove, planningGroupId);
  }, [move, planningGroupId]);

  // ← FIXED: previously built `updatedSchedule` (SessionSlotOut[]) and passed
  //   it to hydrateSchedule via an unsafe `as unknown as typeof state.schedule`
  //   cast. That cast doesn't rename fields — SessionSlotOut uses
  //   `learner_group_id` while SessionSlot expects `group_id` — so the group
  //   silently came through as 0 downstream. Now we build a real,
  //   correctly-shaped SessionSlot[] instead of casting, and we carry
  //   planning_group_id through too (was dropped here before).
  const handleConfirmMove = useCallback(async (adminNote?: string) => {
    const result = await move.confirmMove(adminNote);
    if (result?.success && move.pendingMove) {
      const target  = move.pendingMove.target;
      const movedId = move.pendingMove.slot_id;

      const updatedLocal: SessionSlotOut[] = localSchedule.map(s =>
        (s.id ?? s.session_number) === movedId
          ? {
              ...s,
              start_time:     target.start_time,
              end_time:       target.end_time,
              suggested_day:  `Week ${target.week} — ${target.day}`,
              suggested_time: target.time_slot,
              status:         "draft",   // backend resets status to draft on move
              is_validated:   false,
            }
          : s
      );
      setLocalSchedule(updatedLocal);

      // Build a real SessionSlot[] (not a lossy cast) to keep state.schedule in sync
      const updatedForState: SessionSlot[] = updatedLocal.map(s => ({
        id: s.id,
        planning_group_id: s.planning_group_id ?? planningGroupId,
        session_number: s.session_number,
        course_id: s.course_id,
        course_title: s.course_title,
        trainer_id: s.trainer_id,
        trainer_name: s.trainer_name,
        room_id: s.room_id,
        room_name: s.room_name,
        group_id: s.learner_group_id,
        group_name: s.group_name,
        suggested_day: s.suggested_day,
        suggested_time: s.suggested_time,
        reasoning: s.reasoning,
        start_time: s.start_time,
        end_time: s.end_time,
        status: s.status as SlotStatus,
        is_validated: s.is_validated,
        quality_score: s.quality_score,
        pedagogical_audit_score: s.pedagogical_audit_score,
      }));

      hydrateSchedule(updatedForState, state.constraints);
      setHitlStatus("pending");   // move resets validation
    }
  }, [move, localSchedule, hydrateSchedule, state.constraints, planningGroupId]);

  // =============================================================================
  //  Render
  // =============================================================================

  return (
    <div className="min-h-screen bg-gray-50">

      {/* ── Nav ─────────────────────────────────────────────────────────────── */}
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-linear-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-md">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">ScheduleForge</h1>
                <p className="text-xs text-gray-500">AI Planning Studio</p>
              </div>
            </div>

            {hasSchedule && (
              <div className="flex items-center gap-2">
                <div className="h-8 w-px bg-gray-200" />
                <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
                  {(["global","group","trainer"] as const).map(v => {
                    const icons  = { global: <LayoutGrid className="w-4 h-4" />, group: <Users className="w-4 h-4" />, trainer: <GraduationCap className="w-4 h-4" /> };
                    const labels = { global: "Timeline", group: "Groups", trainer: "Trainers" };
                    return (
                      <button key={v} onClick={() => setMode(v)}
                        className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all flex items-center gap-2 ${mode === v ? "bg-white text-gray-900 shadow-sm" : "text-gray-600 hover:text-gray-900"}`}>
                        {icons[v]}{labels[v]}
                      </button>
                    );
                  })}
                  <button onClick={() => setMode("dnd")}
                    className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all flex items-center gap-2 ${mode === "dnd" ? "bg-white text-gray-900 shadow-sm" : "text-gray-600 hover:text-gray-900"}`}>
                    <Move className="w-4 h-4" />Drag & Drop
                  </button>
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center gap-3">
            {hasSchedule && (
              <>
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => setIsSearchOpen((open) => !open)}
                    className={`p-2 rounded-lg ${isSearchOpen ? "bg-blue-50" : "hover:bg-gray-100"}`}
                    aria-label="Search schedule"
                    title="Search schedule"
                  >
                    <Search className="w-4 h-4 text-gray-600" />
                  </button>
                  {isSearchOpen && (
                    <div className="absolute right-0 top-full z-50 mt-2 rounded-xl border border-gray-200 bg-white p-2 shadow-lg">
                      <input
                        autoFocus
                        value={searchQuery}
                        onChange={(event) => setSearchQuery(event.target.value)}
                        placeholder="Search schedule..."
                        aria-label="Search schedule"
                        className="w-64 rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
                      />
                    </div>
                  )}
                </div>
                <NotificationBell />
                <div className="h-8 w-px bg-gray-200" />
              </>
            )}
            <button onClick={() => navigate("/pedagogical-audit", { state: { preloadedSchedule: localSchedule, preloadedConstraints: state.constraints, planningGroupId } })}
              className="inline-flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-1.5 text-sm font-medium text-emerald-700 hover:bg-emerald-100">
              <ClipboardCheck className="w-4 h-4" />Pedagogical report
            </button>
            <button onClick={() => navigate("/anomaly")}
              className="inline-flex items-center gap-2 rounded-lg border border-rose-200 bg-rose-50 px-4 py-1.5 text-sm font-medium text-rose-700 hover:bg-rose-100">
              <CircleAlert className="w-4 h-4" />Anomaly report
            </button>
            <button
              type="button"
              onClick={() => navigate("/user")}
              className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
              aria-label="Open user profile"
              title="User profile"
            >
              <UserRound className="w-4 h-4" />User
            </button>
          </div>
        </div>
      </nav>

      <div className="px-8 py-6">
        <div className="max-w-400 mx-auto space-y-6">

          {/* Error */}
          {(hitlError || validation.error || regeneration.error || move.error) && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-3">
              <CircleAlert className="w-5 h-5 text-red-600" />
              <span className="text-red-700 font-medium">{hitlError || validation.error || regeneration.error || move.error}</span>
            </div>
          )}

          {/* Status */}
          {state.status === "loading" && (
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-center justify-center gap-3">
              <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
              <span className="text-blue-700 font-medium">AI is processing your request...</span>
            </div>
          )}
          {state.status === "error" && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center justify-center gap-3">
              <CircleAlert className="w-5 h-5 text-red-600" />
              <span className="text-red-700 font-medium">{state.error}</span>
            </div>
          )}

          {/* Success header */}
          {(state.status === "success" || state.status === "validated" || hitlStatus === "pending" || hitlStatus === "validated") && hasSchedule && (
            <div className="bg-linear-to-r from-emerald-50 to-teal-50 border border-emerald-200 rounded-xl p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
                    <Check className="w-6 h-6 text-emerald-600" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      {hitlStatus === "validated" ? "Schedule Validated" : "Schedule Generated Successfully"}
                    </h3>
                    <p className="text-sm text-gray-600">
                      {hitlStatus === "validated" ? "This planning has been confirmed." : "Review, validate or adjust below."}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2 flex-wrap justify-end">
                  {/* HITL — pending only */}
                  {hitlStatus === "pending" && (
                    <>
                      <button onClick={handleValidate} disabled={validation.loading}
                        className="px-4 py-2 bg-emerald-600 text-white rounded-xl font-medium hover:bg-emerald-700 flex items-center gap-2 text-sm disabled:opacity-60">
                        {validation.loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                        Validate
                      </button>
                      <button onClick={() => setDialog("regenerate")} disabled={validation.loading}
                        className="px-4 py-2 bg-violet-100 border border-violet-300 text-violet-800 rounded-xl font-medium hover:bg-violet-200 flex items-center gap-2 text-sm disabled:opacity-60">
                        <Settings2 className="w-4 h-4" />Modify
                      </button>
                      <button onClick={() => setDialog("reject")} disabled={validation.loading}
                        className="px-4 py-2 bg-rose-100 border border-rose-300 text-rose-800 rounded-xl font-medium hover:bg-rose-200 flex items-center gap-2 text-sm disabled:opacity-60">
                        <XCircle className="w-4 h-4" />Reject
                      </button>
                    </>
                  )}
                  {canExport && (
                    <button onClick={handleExport} disabled={isExporting}
                      className="px-4 py-2 bg-gray-800 text-white rounded-xl font-medium hover:bg-gray-900 flex items-center gap-2 text-sm">
                      {isExporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                      Export CSV
                    </button>
                  )}
                  <button onClick={handleRefresh} className="p-2.5 hover:bg-white rounded-xl">
                    <RefreshCw className="w-4 h-4 text-gray-600" />
                  </button>
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-4 gap-4 mt-6">
                {[["Total Sessions", totalSessions], ["Training Days", totalDays], ["Active Courses", totalCourses], ["Weeks", totalWeeks]].map(([label, val]) => (
                  <div key={label as string} className="bg-white rounded-lg p-4">
                    <p className="text-xs text-gray-500 mb-1">{label}</p>
                    <p className="text-2xl font-bold text-gray-900">{val}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* After rejection */}
          {hitlStatus === "rejected" && (
            <div className="bg-rose-50 border border-rose-200 rounded-xl p-6 text-center space-y-3">
              <p className="text-sm font-semibold text-rose-800">Planning rejected. Generate a new proposal?</p>
              <div className="flex justify-center gap-3">
                <button onClick={() => setDialog("regenerate")} disabled={regeneration.regenerating}
                  className="rounded-xl bg-violet-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-violet-700 disabled:opacity-60 flex items-center gap-2">
                  {regeneration.regenerating ? <><Loader2 className="w-4 h-4 animate-spin"/>Generating…</> : <><RefreshCw className="w-4 h-4"/>New proposal</>}
                </button>
                <button onClick={() => { setHitlStatus("idle"); handleReset(); }}
                  className="rounded-xl border border-gray-200 bg-white px-6 py-2.5 text-sm font-semibold text-gray-700 hover:bg-gray-50">
                  Start fresh
                </button>
              </div>
            </div>
          )}

          {/* Constraints */}
          {state.constraints && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Pin className="w-4 h-4 text-gray-500" />
                <h4 className="text-sm font-medium text-gray-700">Active Constraints</h4>
              </div>
              <div className="flex flex-wrap gap-2">
                {state.constraints.forbidden_days?.length > 0 && (
                  <span className="px-3 py-1.5 bg-white border border-gray-200 rounded-lg text-sm text-gray-700">
                    No sessions on {state.constraints.forbidden_days.join(", ")}
                  </span>
                )}
                {state.constraints.session_duration_override && (
                  <span className="px-3 py-1.5 bg-white border border-gray-200 rounded-lg text-sm text-gray-700">
                    {state.constraints.session_duration_override}h sessions
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Schedule views */}
          {hasSchedule && (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              <div className="p-6 border-b border-gray-200 flex items-center justify-between">
                <h3 className="font-semibold text-gray-900">
                  {mode === "global"   && "Training Schedule Timeline"}
                  {mode === "group"    && "Schedule by Groups"}
                  {mode === "trainer"  && "Schedule by Trainers"}
                  {mode === "dnd"      && "Drag & Drop — Rearrange Sessions"}
                </h3>
                <div className="flex items-center gap-2">
                  {mode === "dnd" && (
                    <span className="px-3 py-1 rounded-lg bg-violet-100 text-violet-700 text-xs font-semibold">
                      ⠿ Drag sessions to move
                    </span>
                  )}
                  {mode !== "dnd" && (
                    <button onClick={() => setShowReasoning(!showReasoning)}
                      className={`px-3 py-1.5 text-xs font-medium rounded-lg flex items-center gap-2 ${showReasoning ? "bg-blue-100 text-blue-700" : "bg-gray-100 text-gray-600"}`}>
                      {showReasoning ? "Hide" : "Show"} Reasoning
                    </button>
                  )}
                  <button className="p-1.5 hover:bg-gray-100 rounded-lg">
                    <MoreHorizontal className="w-4 h-4 text-gray-500" />
                  </button>
                </div>
              </div>

              <div className="overflow-x-auto">
                {mode === "global"   && <PlanningTable schedule={filteredSchedule} mode="global" showReasoning={showReasoning} />}
                {(mode === "group" || mode === "trainer") && <GroupedPlanningView schedule={filteredSchedule} mode={mode} showReasoning={showReasoning} />}
                {mode === "dnd" && localSchedule.length > 0 && (
                  <div className="p-4">
                    <ScheduleGrid
                      sessions        = {localSchedule}
                      planningGroupId = {planningGroupId}
                      currentWeek     = {currentWeek}
                      totalWeeks      = {totalWeeks}
                      draggingSlotId  = {move.draggingSlotId}
                      onWeekChange    = {setCurrentWeek}
                      onDragStart     = {handleDragStart}
                      onDragEnd       = {move.endDrag}
                      onDrop          = {handleDrop}
                    />
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Empty state */}
          {!hasSchedule && state.status === "idle" && hitlStatus !== "rejected" && (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-16 text-center">
              <div className="w-20 h-20 bg-blue-50 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <TrendingUp className="w-10 h-10 text-blue-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Waiting for a Generated Schedule</h3>
              <p className="text-gray-500 max-w-md mx-auto">
                Create the plan from the constraint page first.
              </p>
            </div>
          )}

        </div>
      </div>

      {/* ── Modals ──────────────────────────────────────────────────────────── */}
      {move.impact && move.pendingMove && (
        <ImpactPanel pendingMove={move.pendingMove} impact={move.impact} isApplying={move.isApplying} onConfirm={handleConfirmMove} onCancel={move.cancelMove} />
      )}
      {dialog === "reject" && (
        <ValidationDialog mode="reject" loading={validation.loading} onConfirm={handleRejectConfirm} onCancel={() => setDialog("none")} />
      )}
      {dialog === "regenerate" && (
        <RegenerationDialog attempt={attempt + 1} regenerating={regeneration.regenerating} onRegenerate={handleRegenerate} onCancel={() => setDialog("none")} />
      )}
    </div>
  );
}