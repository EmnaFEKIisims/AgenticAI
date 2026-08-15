import { useState, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";

import ConstraintForm       from "../components/constraint/ConstraintForm";
import ValidationPanel      from "../components/constraint/ValidationPanel";
import ConstraintSummary    from "../components/constraint/ConstraintSummary";
import ConstraintPreview    from "../components/constraint/ConstraintPreview";
import LoadingOverlay       from "../components/constraint/LoadingOverlay";

import {
  analyzeConstraints,
  mapValidationResult,
  mapSummaryData,
} from "../services/constraintService";
import { runPlanningWithConstraints } from "../services/planningService";

import type {
  ConstraintFormValue,
  ConstraintAgentState,
  ConstraintAnalyzeResponse,
} from "../types/constraintTypes";


// =============================================================================
//  Initial state
// =============================================================================

const INITIAL_FORM: ConstraintFormValue = {
  pedagogicalText: "",
  userText:        "",
};

const INITIAL_STATE: ConstraintAgentState = {
  status:     "idle",
  response:   null,
  summary:    null,
  validation: null,
  error:      null,
};


// =============================================================================
//  PAGE
// =============================================================================

export default function ConstraintPage() {
  const navigate = useNavigate();
  const [form,  setForm]  = useState<ConstraintFormValue>(INITIAL_FORM);
  const [state, setState] = useState<ConstraintAgentState>(INITIAL_STATE);
  const [isCreatingPlan, setIsCreatingPlan] = useState(false);
  const requestInFlight = useRef(false);

  const isLoading = state.status === "loading";
  const isBusy = isLoading || isCreatingPlan;
  const hasResult = state.status === "success" && state.response !== null;
  const canCreatePlan =
    hasResult &&
    state.response?.planning_dict &&
    state.validation &&
    ["valid", "warning"].includes(state.validation.status);

  // ── Generate — calls ConstraintAgent backend ────────────────────────────────
  const handleGenerate = useCallback(async () => {
    if (requestInFlight.current) return;
    requestInFlight.current = true;
    setState({ ...INITIAL_STATE, status: "loading" });

    try {
      const response: ConstraintAnalyzeResponse = await analyzeConstraints(
        form.pedagogicalText,
        form.userText,
      );

      const validation = mapValidationResult(response.validation);

      setState({
        status:     "success",
        response,
        summary:    mapSummaryData(response.planning_dict),
        validation,
        error:      null,
      });

      // If constraints are valid (or warning-only), generate planning immediately.
      if (["valid", "warning"].includes(validation.status)) {
        setIsCreatingPlan(true);
        try {
          const planningResponse = await runPlanningWithConstraints(response.planning_dict);
          navigate("/planning", {
            state: {
              preloadedSchedule: planningResponse.schedule,
              preloadedConstraints: planningResponse.final_constraints,
            },
          });
        } catch (err) {
          setState((prev) => ({
            ...prev,
            error: err instanceof Error ? err.message : "Planning generation failed",
          }));
        } finally {
          setIsCreatingPlan(false);
        }
      }
    } catch (err) {
      setState({
        ...INITIAL_STATE,
        status: "error",
        error:  err instanceof Error ? err.message : "Unexpected error",
      });
      setIsCreatingPlan(false);
    } finally {
      requestInFlight.current = false;
    }
  }, [form, navigate]);

  // ── Reset ───────────────────────────────────────────────────────────────────
  const handleReset = useCallback(() => {
    setForm(INITIAL_FORM);
    setState(INITIAL_STATE);
    setIsCreatingPlan(false);
  }, []);


  // =============================================================================
  //  RENDER
  // =============================================================================

  return (
    <div className="min-h-screen bg-slate-50">

      {/* Loading overlay */}
      <LoadingOverlay
        visible={isBusy}
        step={isCreatingPlan ? "Generating planning..." : "Analyzing constraints..."}
      />

      {/* Header */}
      <header className="border-b border-slate-200 bg-white px-6 py-5">
        <div className="mx-auto max-w-5xl">
          <div className="flex items-center gap-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-900 text-white text-lg">
              📋
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900">Constraint Agent</h1>
              <p className="text-sm text-slate-500">
                ISO + pedagogical + user constraints — analyzed, merged and validated
              </p>
            </div>
            {hasResult && (
              <span
                className={`ml-auto rounded-full border px-4 py-1 text-xs font-semibold ${
                  state.validation?.is_valid
                    ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                    : "border-rose-200 bg-rose-50 text-rose-700"
                }`}
              >
                {state.validation?.status?.toUpperCase() ?? ""}
              </span>
            )}
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="mx-auto max-w-5xl px-6 py-8 space-y-6">

        {/* Error banner */}
        {state.error && (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-800">
            ❌ {state.error}
          </div>
        )}

        {/* Two-column layout on large screens */}
        <div className="grid gap-6 lg:grid-cols-[1fr_400px]">

          {/* LEFT — Form + Results */}
          <div className="space-y-6">

            {/* Constraint Form */}
            <ConstraintForm
              value={form}
              onChange={setForm}
              onGenerate={handleGenerate}
              onReset={handleReset}
              disabled={isBusy}
              loading={isBusy}
            />

            {/* Validation Panel — shown after generation */}
            {hasResult && state.validation && (
              <ValidationPanel result={state.validation} />
            )}

            {/* Constraint Summary — shown when valid or warning */}
            {hasResult && state.summary && (
              <ConstraintSummary data={state.summary} />
            )}

            {/* JSON Preview */}
            {hasResult && state.response && (
              <ConstraintPreview data={state.response.planning_dict} />
            )}

          </div>

          {/* RIGHT — Info sidebar */}
          <aside className="space-y-4">

            {/* How it works */}
            <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500 mb-3">
                Pipeline
              </p>
              <div className="space-y-3">
                {[
                  { step: "1", label: "ISO rules",          desc: "Loaded from DB automatically",       color: "bg-violet-100 text-violet-700" },
                  { step: "2", label: "Pedagogical rules",  desc: "LLM extracts from your text",        color: "bg-emerald-100 text-emerald-700" },
                  { step: "3", label: "User constraints",   desc: "LLM extracts from your text",        color: "bg-sky-100 text-sky-700" },
                  { step: "4", label: "Merge",              desc: "ISO hard rules take priority",        color: "bg-amber-100 text-amber-700" },
                  { step: "5", label: "Validate",           desc: "ISO limits + business rules checked", color: "bg-slate-100 text-slate-700" },
                ].map(({ step, label, desc, color }) => (
                  <div key={step} className="flex items-start gap-3">
                    <span className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold ${color}`}>
                      {step}
                    </span>
                    <div>
                      <p className="text-sm font-semibold text-slate-800">{label}</p>
                      <p className="text-xs text-slate-500">{desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Tips */}
            <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500 mb-3">
                Tips
              </p>
              <ul className="space-y-2 text-sm text-slate-600">
                <li>💡 Leave both fields empty to use only ISO + DB rules.</li>
                <li>💡 After generating, use the <strong>planning_dict</strong> for <code className="rounded bg-slate-100 px-1 text-xs">POST /planning/run/with-constraints</code>.</li>
                <li>💡 Warnings are non-blocking — planning still runs.</li>
                <li>💡 INVALID or CONFLICT issues must be fixed first.</li>
              </ul>
            </div>

          </aside>
        </div>
      </main>
    </div>
  );
}