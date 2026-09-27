import { useState, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { ShieldCheck } from "lucide-react";

import ConstraintForm    from "../components/constraint/ConstraintForm";
import ValidationPanel   from "../components/constraint/ValidationPanel";
import ConstraintSummary from "../components/constraint/ConstraintSummary";
import ConstraintPreview from "../components/constraint/ConstraintPreview";
import LoadingOverlay    from "../components/constraint/LoadingOverlay";

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

export default function ConstraintPage() {
  const navigate = useNavigate();
  const [form,  setForm]  = useState<ConstraintFormValue>(INITIAL_FORM);
  const [state, setState] = useState<ConstraintAgentState>(INITIAL_STATE);
  const [isCreatingPlan, setIsCreatingPlan] = useState(false);
  const requestInFlight = useRef(false);

  const isLoading = state.status === "loading";
  const isBusy = isLoading || isCreatingPlan;
  const hasResult = state.status === "success" && state.response !== null;

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

      if (["valid", "warning"].includes(validation.status)) {
        setIsCreatingPlan(true);
        try {
          const planningResponse = await runPlanningWithConstraints(response.planning_dict);
          navigate("/planning", {
            state: {
              preloadedSchedule:    planningResponse.schedule,
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

  const handleReset = useCallback(() => {
    setForm(INITIAL_FORM);
    setState(INITIAL_STATE);
    setIsCreatingPlan(false);
  }, []);

  return (
    <div className="min-h-screen bg-linear-to-br from-slate-50 via-white to-slate-50">
      <LoadingOverlay
        visible={isBusy}
        step={isCreatingPlan ? "Generating planning..." : "Analyzing constraints..."}
      />

      {/* Header */}
      <header className="border-b border-slate-200 bg-white/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-4xl items-center gap-4 px-6 py-5">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-slate-900 text-white shadow-sm">
            <ShieldCheck className="h-5 w-5" aria-hidden="true" />
          </span>
          <div className="min-w-0 flex-1">
            <h1 className="text-lg font-semibold tracking-tight text-slate-900">
              Constraint Agent
            </h1>
            <p className="text-sm text-slate-500">
              Describe your needs, and the agent will build the planning.
            </p>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="mx-auto max-w-4xl space-y-6 px-6 py-10">
        {state.error && (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-800 shadow-sm">
            {state.error}
          </div>
        )}

        <ConstraintForm
          value={form}
          onChange={setForm}
          onGenerate={handleGenerate}
          onReset={handleReset}
          disabled={isBusy}
          loading={isBusy}
        />

        {hasResult && state.validation && (
          <ValidationPanel result={state.validation} />
        )}

        {hasResult && state.summary && (
          <ConstraintSummary data={state.summary} />
        )}

        {hasResult && state.response && (
          <ConstraintPreview data={state.response.planning_dict} />
        )}
      </main>
    </div>
  );
}