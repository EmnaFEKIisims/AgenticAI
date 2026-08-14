import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { usePlanning } from "../hooks/usePlanning";
import PlanningTable from "../components/planning/PlanningTable";
import GroupedPlanningView from "../components/planning/GroupedPlanningView";
import CalendarGridView from "../components/planning/CalendarGridView";
import {
  CalendarDays,
  Check,
  CircleAlert,
  Download,
  GraduationCap,
  LayoutGrid,
  Loader2,
  Pin,
  RefreshCw,
  Sparkles,
  Users,
  Filter,
  MoreHorizontal,
  Search,
  TrendingUp,
  ClipboardCheck,
} from "lucide-react";

type PlanningViewMode = "global" | "group" | "trainer" | "calendar";

export default function PlanningPage() {
  const [mode, setMode] = useState<PlanningViewMode>("calendar");
  const [showReasoning, setShowReasoning] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const {
    state,
    userInput,
    isExporting,
    hasSchedule,
    canValidate,
    canExport,
    isLoading,
    sessionsByDay,
    sessionsByCourse,
    handleValidate,
    handleExport,
    handleRefresh,
    handleReset,
    hydrateSchedule,
  } = usePlanning();

  useEffect(() => {
    const navState = location.state as {
      preloadedSchedule?: unknown;
      preloadedConstraints?: unknown;
    } | null;

    if (Array.isArray(navState?.preloadedSchedule) && navState.preloadedSchedule.length > 0) {
      hydrateSchedule(
        navState.preloadedSchedule as typeof state.schedule,
        (navState.preloadedConstraints as typeof state.constraints) ?? null,
      );
      return;
    }

    void handleRefresh();
  }, [handleRefresh, hydrateSchedule, location.state]);

  // Calculate stats
  const totalSessions = state.schedule.length;
  const totalDays = Object.keys(sessionsByDay).length;
  const totalCourses = Object.keys(sessionsByCourse).length;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Navigation Bar */}
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="px-8 py-4">
          <div className="flex items-center justify-between">
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
                    <button
                      onClick={() => setMode("calendar")}
                      className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all flex items-center gap-2 ${
                        mode === "calendar" 
                          ? "bg-white text-gray-900 shadow-sm" 
                          : "text-gray-600 hover:text-gray-900"
                      }`}
                    >
                      <CalendarDays className="w-4 h-4" />
                      Calendar
                    </button>
                    <button
                      onClick={() => setMode("global")}
                      className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all flex items-center gap-2 ${
                        mode === "global" 
                          ? "bg-white text-gray-900 shadow-sm" 
                          : "text-gray-600 hover:text-gray-900"
                      }`}
                    >
                      <LayoutGrid className="w-4 h-4" />
                      Timeline
                    </button>
                    <button
                      onClick={() => setMode("group")}
                      className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all flex items-center gap-2 ${
                        mode === "group" 
                          ? "bg-white text-gray-900 shadow-sm" 
                          : "text-gray-600 hover:text-gray-900"
                      }`}
                    >
                      <Users className="w-4 h-4" />
                      Groups
                    </button>
                    <button
                      onClick={() => setMode("trainer")}
                      className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all flex items-center gap-2 ${
                        mode === "trainer" 
                          ? "bg-white text-gray-900 shadow-sm" 
                          : "text-gray-600 hover:text-gray-900"
                      }`}
                    >
                      <GraduationCap className="w-4 h-4" />
                      Trainers
                    </button>
                  </div>
                </div>
              )}
            </div>

            <div className="flex items-center gap-3">
              {hasSchedule && (
                <>
                  <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                    <Search className="w-4 h-4 text-gray-600" />
                  </button>
                  <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                    <Filter className="w-4 h-4 text-gray-600" />
                  </button>
                  <div className="h-8 w-px bg-gray-200" />
                </>
              )}
              <button
                type="button"
                onClick={() =>
                  navigate("/pedagogical-audit", {
                    state: {
                      preloadedSchedule: state.schedule,
                      preloadedConstraints: state.constraints,
                    },
                  })
                }
                className="inline-flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-1.5 text-sm font-medium text-emerald-700 transition-colors hover:bg-emerald-100"
              >
                <ClipboardCheck className="w-4 h-4" />
                Pedagogical report
              </button>
              <button
                type="button"
                onClick={(event) => {
                  event.preventDefault();
                  navigate("/anomaly");
                }}
                className="inline-flex items-center gap-2 rounded-lg border border-rose-200 bg-rose-50 px-4 py-1.5 text-sm font-medium text-rose-700 transition-colors hover:bg-rose-100"
              >
                <CircleAlert className="w-4 h-4" />
                Anomaly report
              </button>
              <button
                type="button"
                onClick={handleReset}
                className="text-sm text-gray-600 hover:text-gray-900 px-3 py-1.5 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Clear All
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="px-8 py-6">
        <div className="max-w-400 mx-auto">
          {/* Status Display */}
          {state.status !== "idle" && state.status !== "success" && state.status !== "validated" && (
            <div className="mb-6">
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
            </div>
          )}

          {/* Success Header with Stats */}
          {(state.status === "success" || state.status === "validated") && (
            <div className="mb-6">
              <div className="bg-linear-to-r from-emerald-50 to-teal-50 border border-emerald-200 rounded-xl p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
                      <Check className="w-6 h-6 text-emerald-600" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">
                        {state.status === "validated" ? "Schedule Validated" : "Schedule Generated Successfully"}
                      </h3>
                      <p className="text-sm text-gray-600">
                        Your training schedule is ready for review
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {canValidate && (
                      <button
                        onClick={handleValidate}
                        className="px-5 py-2.5 bg-emerald-600 text-white rounded-xl font-medium hover:bg-emerald-700 transition-colors flex items-center gap-2 shadow-sm"
                      >
                        <Check className="w-4 h-4" />
                        Validate Schedule
                      </button>
                    )}
                    {canExport && (
                      <button
                        onClick={handleExport}
                        disabled={isExporting}
                        className="px-5 py-2.5 bg-gray-800 text-white rounded-xl font-medium hover:bg-gray-900 transition-colors flex items-center gap-2 shadow-sm"
                      >
                        {isExporting ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Download className="w-4 h-4" />
                        )}
                        Export CSV
                      </button>
                    )}
                    <button
                      onClick={handleRefresh}
                      className="p-2.5 hover:bg-white rounded-xl transition-colors"
                    >
                      <RefreshCw className="w-4 h-4 text-gray-600" />
                    </button>
                  </div>
                </div>

                {/* Stats Cards */}
                <div className="grid grid-cols-3 gap-4 mt-6">
                  <div className="bg-white rounded-lg p-4">
                    <p className="text-xs text-gray-500 mb-1">Total Sessions</p>
                    <p className="text-2xl font-bold text-gray-900">{totalSessions}</p>
                  </div>
                  <div className="bg-white rounded-lg p-4">
                    <p className="text-xs text-gray-500 mb-1">Training Days</p>
                    <p className="text-2xl font-bold text-gray-900">{totalDays}</p>
                  </div>
                  <div className="bg-white rounded-lg p-4">
                    <p className="text-xs text-gray-500 mb-1">Active Courses</p>
                    <p className="text-2xl font-bold text-gray-900">{totalCourses}</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Active Constraints */}
          {state.constraints && (
            <div className="mb-6">
              <div className="flex items-center gap-2 mb-3">
                <Pin className="w-4 h-4 text-gray-500" />
                <h4 className="text-sm font-medium text-gray-700">Active Constraints</h4>
              </div>
              <div className="flex flex-wrap gap-2">
                {state.constraints.forbidden_days.length > 0 && (
                  <span className="px-3 py-1.5 bg-white border border-gray-200 rounded-lg text-sm text-gray-700">
                    No sessions on {state.constraints.forbidden_days.join(", ")}
                  </span>
                )}
                {state.constraints.session_duration_override && (
                  <span className="px-3 py-1.5 bg-white border border-gray-200 rounded-lg text-sm text-gray-700">
                    {state.constraints.session_duration_override}h sessions
                  </span>
                )}
                {state.constraints.min_room_capacity && (
                  <span className="px-3 py-1.5 bg-white border border-gray-200 rounded-lg text-sm text-gray-700">
                    Min {state.constraints.min_room_capacity} capacity
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Main Schedule Display */}
          {hasSchedule && (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-gray-900">
                    {mode === "calendar" && "Calendar Grid View"}
                    {mode === "global" && "Training Schedule Timeline"}
                    {mode === "group" && "Schedule by Groups"}
                    {mode === "trainer" && "Schedule by Trainers"}
                  </h3>
                  <div className="flex items-center gap-2">
                    {mode !== "calendar" && (
                      <button
                        onClick={() => setShowReasoning(!showReasoning)}
                        className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors flex items-center gap-2 ${
                          showReasoning
                            ? "bg-blue-100 text-blue-700"
                            : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                        }`}
                      >
                        {showReasoning ? "Hide" : "Show"} Reasoning
                      </button>
                    )}
                    <button className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors">
                      <MoreHorizontal className="w-4 h-4 text-gray-500" />
                    </button>
                  </div>
                </div>
              </div>
              
              <div className="overflow-x-auto">
                <div className="min-w-full">
                  {mode === "calendar" && <CalendarGridView sessionsByDay={sessionsByDay} />}
                  {mode === "global" && <PlanningTable schedule={state.schedule} mode="global" showReasoning={showReasoning} />}
                  {mode !== "global" && mode !== "calendar" && <GroupedPlanningView schedule={state.schedule} mode={mode} showReasoning={showReasoning} />}
                </div>
              </div>
            </div>
          )}

          {/* Empty State */}
          {!hasSchedule && state.status === "idle" && (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-16 text-center">
              <div className="w-20 h-20 bg-blue-50 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <TrendingUp className="w-10 h-10 text-blue-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Waiting for a Generated Schedule
              </h3>
              <p className="text-gray-500 max-w-md mx-auto">
                Create the plan from the constraint page first. This page will show the generated schedule once it is available.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}