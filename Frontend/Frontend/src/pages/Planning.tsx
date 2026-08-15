import { useEffect, useState, useCallback } from "react";
import { useLocation, useNavigate }         from "react-router-dom";
import { usePlanning }                      from "../hooks/usePlanning";

// ── Existing view components ─────────────────────────────────────────────────
import PlanningTable        from "../components/planning/PlanningTable";
import GroupedPlanningView  from "../components/planning/GroupedPlanningView";
import CalendarGridView     from "../components/planning/CalendarGridView";

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
import type { SessionSlot } from "../types/planning";
import type { HITLStatus }     from "../types/planningValidation";

import {
  CalendarDays, Check, CircleAlert, Download, GraduationCap,
  LayoutGrid, Loader2, Pin, RefreshCw, Sparkles, Users,
  Filter, MoreHorizontal, Search, TrendingUp, ClipboardCheck,
  Move, XCircle, Settings2,
} from "lucide-react";

type PlanningViewMode = "global" | "group" | "trainer" | "calendar" | "dnd";

export default function PlanningPage() {

  // ── Existing state ──────────────────────────────────────────────────────────
  const [mode,          setMode]          = useState<PlanningViewMode>("calendar");
  const [showReasoning, setShowReasoning] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  // ── NEW state ────────────────────────────────────────────────────────────────
  const [planningGroupId, setPlanningGroupId] = useState("");
  const [hitlStatus,      setHitlStatus]      = useState<HITLStatus>("idle");
  const [attempt,         setAttempt]         = useState(1);
  const [currentWeek,     setCurrentWeek]     = useState(1);
  const [localSchedule,   setLocalSchedule]   = useState<SessionSlotOut[]>([]);
  const [dialog,          setDialog]          = useState<"none"|"reject"|"modify"|"regenerate">("none");

  // ── Existing hook ────────────────────────────────────────────────────────────
  const {
    state, isExporting, hasSchedule,
    canExport, isLoading, sessionsByDay, sessionsByCourse,
    handleExport, handleRefresh, handleReset, hydrateSchedule,
  } = usePlanning();

  // ── NEW hooks ────────────────────────────────────────────────────────────────
  const validation   = usePlanningValidation();
  const regeneration = usePlanningRegeneration();
  const move         = useScheduleMove();

  // ── Sync localSchedule ───────────────────────────────────────────────────────
  useEffect(() => {
    if (state.schedule?.length) {
      // Convert SessionSlot[] -> SessionSlotOut[]
      const mapped: SessionSlotOut[] = state.schedule.map((s: SessionSlot) => ({
        id: undefined,
        session_number: s.session_number,
        course_id: s.course_id,
        course_title: s.course_title,
        trainer_id: s.trainer_id,
        trainer_name: s.trainer_name,
        room_id: s.room_id,
        room_name: s.room_name,
        group_name: s.group_name,
        learner_group_id: (s as any).group_id ?? 0,
        suggested_day: s.suggested_day,
        suggested_time: s.suggested_time,
        start_time: "",
        end_time: "",
        status: "draft",
        is_validated: false,
        quality_score: 0,
        pedagogical_audit_score: 0,
        reasoning: s.reasoning,
      }));
      setLocalSchedule(mapped);
      if (hitlStatus === "idle") setHitlStatus("pending");
    }
  }, [state.schedule]);

  // ── Hydrate from navigation state ────────────────────────────────────────────
  useEffect(() => {
    const navState = location.state as {
      preloadedSchedule?:    unknown;
      preloadedConstraints?: unknown;
      planningGroupId?:      string;
    } | null;

    if (navState?.planningGroupId) setPlanningGroupId(navState.planningGroupId);

    if (Array.isArray(navState?.preloadedSchedule) && navState.preloadedSchedule.length > 0) {
      // navState.preloadedSchedule may be SessionSlot[] or SessionSlotOut[] depending on navigation source.
      const pre = navState.preloadedSchedule as unknown[];
      const asSessionSlots: SessionSlot[] = pre.map((p: any) => ({
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
      }));

      hydrateSchedule(asSessionSlots, (navState.preloadedConstraints as typeof state.constraints) ?? null);
      setHitlStatus("pending");
      return;
    }
    void handleRefresh();
  }, []);   // ← run once only

  // ── Stats ────────────────────────────────────────────────────────────────────
  const totalSessions = state.schedule.length;
  const totalDays     = Object.keys(sessionsByDay).length;
  const totalCourses  = Object.keys(sessionsByCourse).length;
  const totalWeeks    = localSchedule.length > 0
    ? Math.max(...localSchedule.map(s => parseInt(s.suggested_day?.match(/Week\s+(\d+)/i)?.[1] ?? "1")))
    : 1;

  // =============================================================================
  //  HITL Handlers — use planningManagementService (correct endpoints)
  // =============================================================================

  const handleValidate = useCallback(async () => {
    // Uses POST /planning/{group_id}/validate — correct endpoint
    if (planningGroupId) {
      await validation.validate(planningGroupId);
    }
    // Update local UI state — do NOT call old validatePlanning() hook
    setHitlStatus("validated");
  }, [planningGroupId, validation]);

  const handleRejectConfirm = useCallback(async (reason: string) => {
    if (planningGroupId) {
      await validation.reject(planningGroupId, reason);
    }
    setHitlStatus("rejected");
    setLocalSchedule([]);
    setDialog("none");
    handleReset();
  }, [planningGroupId, validation, handleReset]);

  const handleModifyConfirm = useCallback((_text: string) => {
    setDialog("regenerate");
  }, []);

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

  const handleConfirmMove = useCallback(async (adminNote?: string) => {
    const result = await move.confirmMove(adminNote);
    if (result?.success && move.pendingMove) {
      const target = move.pendingMove.target;
      setLocalSchedule(prev => prev.map(s =>
        (s.id ?? s.session_number) === move.pendingMove?.slot_id
          ? { ...s, start_time: target.start_time, end_time: target.end_time,
              suggested_day: `Week ${target.week} — ${target.day}`,
              suggested_time: target.time_slot }
          : s
      ));
      setHitlStatus("pending");
    }
  }, [move]);

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
                  {(["calendar","global","group","trainer"] as const).map(v => {
                    const icons  = { calendar: <CalendarDays className="w-4 h-4" />, global: <LayoutGrid className="w-4 h-4" />, group: <Users className="w-4 h-4" />, trainer: <GraduationCap className="w-4 h-4" /> };
                    const labels = { calendar: "Calendar", global: "Timeline", group: "Groups", trainer: "Trainers" };
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
                <button className="p-2 hover:bg-gray-100 rounded-lg"><Search className="w-4 h-4 text-gray-600" /></button>
                <button className="p-2 hover:bg-gray-100 rounded-lg"><Filter className="w-4 h-4 text-gray-600" /></button>
                <div className="h-8 w-px bg-gray-200" />
              </>
            )}
            <button onClick={() => navigate("/pedagogical-audit", { state: { preloadedSchedule: state.schedule, preloadedConstraints: state.constraints } })}
              className="inline-flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-1.5 text-sm font-medium text-emerald-700 hover:bg-emerald-100">
              <ClipboardCheck className="w-4 h-4" />Pedagogical report
            </button>
            <button onClick={() => navigate("/anomaly")}
              className="inline-flex items-center gap-2 rounded-lg border border-rose-200 bg-rose-50 px-4 py-1.5 text-sm font-medium text-rose-700 hover:bg-rose-100">
              <CircleAlert className="w-4 h-4" />Anomaly report
            </button>
            <button onClick={handleReset} className="text-sm text-gray-600 hover:text-gray-900 px-3 py-1.5 hover:bg-gray-100 rounded-lg">
              Clear All
            </button>
          </div>
        </div>
      </nav>

      <div className="px-8 py-6">
        <div className="max-w-400 mx-auto space-y-6">

          {/* Error */}
          {(validation.error || regeneration.error || move.error) && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-3">
              <CircleAlert className="w-5 h-5 text-red-600" />
              <span className="text-red-700 font-medium">{validation.error || regeneration.error || move.error}</span>
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
                      {hitlStatus === "validated" ? "Schedule Validated ✅" : "Schedule Generated Successfully"}
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
                      <button onClick={() => setDialog("modify")} disabled={validation.loading}
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
                  {mode === "calendar" && "Calendar Grid View"}
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
                  {mode !== "calendar" && mode !== "dnd" && (
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
                {mode === "calendar" && <CalendarGridView sessionsByDay={sessionsByDay} />}
                {mode === "global"   && <PlanningTable schedule={state.schedule} mode="global" showReasoning={showReasoning} />}
                {(mode === "group" || mode === "trainer") && <GroupedPlanningView schedule={state.schedule} mode={mode} showReasoning={showReasoning} />}
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
      {dialog === "modify" && (
        <ValidationDialog mode="modify" loading={false} onConfirm={handleModifyConfirm} onCancel={() => setDialog("none")} />
      )}
      {dialog === "regenerate" && (
        <RegenerationDialog attempt={attempt + 1} regenerating={regeneration.regenerating} onRegenerate={handleRegenerate} onCancel={() => setDialog("none")} />
      )}
    </div>
  );
}