import { useState } from "react";
import type { Constraints, PlanningState, SessionSlot } from "../types/planning";
import { usePlanning } from "../hooks/usePlanning";
import "../styles/planning.css";
import PlanningTable from "../components/planning/PlanningTable";
import GroupedPlanningView from "../components/planning/GroupedPlanningView";
import {
  CalendarDays,
  Check,
  CircleAlert,
  ClipboardList,
  Download,
  GraduationCap,
  LayoutGrid,
  Loader2,
  Pin,
  Play,
  RefreshCw,
  Sparkles,
  Users,
  X,
} from "lucide-react";

type PlanningViewMode = "global" | "group" | "trainer";

function ConstraintInput({
  value,
  onChange,
  disabled,
}: {
  value: string;
  onChange: (v: string) => void;
  disabled: boolean;
}) {
  return (
    <div className="planning-input-card">
      <label className="planning-label">
        <span className="planning-label-icon" aria-hidden="true">
          <ClipboardList size={14} />
        </span>
        Extra Constraints
        <span className="planning-label-sub"> - natural language, English or French (optional)</span>
      </label>
      <textarea
        className={`planning-textarea${disabled ? " planning-textarea-disabled" : ""}`}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        rows={4}
        placeholder={"e.g. No sessions on Friday.\nAhmed available Monday morning only."}
      />
    </div>
  );
}

function StatusBanner({
  status,
  error,
  totalSessions,
}: {
  status: PlanningState["status"];
  error: string | null;
  totalSessions: number;
}) {
  if (status === "idle") return null;
  if (status === "loading") {
    return (
      <div className="planning-banner planning-banner-info">
        <Loader2 size={15} className="planning-inline-icon planning-spin" aria-hidden="true" />
        Generating schedule...
      </div>
    );
  }
  if (status === "error") {
    return (
      <div className="planning-banner planning-banner-error">
        <CircleAlert size={15} className="planning-inline-icon" aria-hidden="true" />
        {error}
      </div>
    );
  }
  if (status === "validated") {
    return (
      <div className="planning-banner planning-banner-success">
        <Check size={15} className="planning-inline-icon" aria-hidden="true" />
        Schedule validated - {totalSessions} session(s) confirmed.
      </div>
    );
  }
  if (status === "success") {
    return (
      <div className="planning-banner planning-banner-success">
        <CalendarDays size={15} className="planning-inline-icon" aria-hidden="true" />
        Schedule ready - {totalSessions} session(s) generated.
      </div>
    );
  }
  return null;
}

function ConstraintsSummary({ constraints }: { constraints: Constraints }) {
  const active: string[] = [];

  if (constraints.forbidden_days.length) {
    active.push(`No ${constraints.forbidden_days.join(", ")}`);
  }
  if (constraints.session_duration_override) {
    active.push(`Session: ${constraints.session_duration_override}h`);
  }
  if (constraints.min_room_capacity) {
    active.push(`Min capacity: ${constraints.min_room_capacity}`);
  }
  if (constraints.room_type_required) {
    active.push(`Room type: ${constraints.room_type_required}`);
  }
  if (constraints.no_parallel_sessions_same_group) {
    active.push("No parallel sessions");
  }

  Object.entries(constraints.trainer_availability).forEach(([name, availability]) => {
    active.push(`${name}: ${availability}`);
  });

  if (!active.length) return null;

  return (
    <div className="planning-constraints-summary">
      <p className="planning-constraints-title">
        <Pin size={13} className="planning-inline-icon" aria-hidden="true" />
        Active constraints
      </p>
      <div className="planning-tag-row">
        {active.map((constraint, index) => (
          <span key={index} className="planning-tag">
            {constraint}
          </span>
        ))}
      </div>
    </div>
  );
}

function ActionBar({
  isLoading,
  isExporting,
  canValidate,
  canExport,
  onRun,
  onValidate,
  onExport,
  onReset,
  onRefresh,
}: {
  isLoading: boolean;
  isExporting: boolean;
  canValidate: boolean;
  canExport: boolean;
  onRun: () => void;
  onValidate: () => void;
  onExport: () => void;
  onReset: () => void;
  onRefresh: () => void;
}) {
  return (
    <div className="planning-action-bar">
      <button className="planning-btn planning-btn-primary" onClick={onRun} disabled={isLoading}>
        {isLoading ? (
          <>
            <Loader2 size={14} className="planning-btn-icon planning-spin" aria-hidden="true" />
            Generating...
          </>
        ) : (
          <>
            <Play size={14} className="planning-btn-icon" aria-hidden="true" />
            Run Planning
          </>
        )}
      </button>

      {canValidate && (
        <button
          className="planning-btn planning-btn-success"
          onClick={onValidate}
          disabled={isLoading}
        >
          <Check size={14} className="planning-btn-icon" aria-hidden="true" />
          Validate
        </button>
      )}

      {canExport && (
        <button
          className="planning-btn planning-btn-export"
          onClick={onExport}
          disabled={isExporting}
        >
          {isExporting ? (
            <>
              <Loader2 size={14} className="planning-btn-icon planning-spin" aria-hidden="true" />
              Exporting...
            </>
          ) : (
            <>
              <Download size={14} className="planning-btn-icon" aria-hidden="true" />
              Export CSV
            </>
          )}
        </button>
      )}

      <button className="planning-btn planning-btn-ghost" onClick={onRefresh} disabled={isLoading}>
        <RefreshCw size={14} className="planning-btn-icon" aria-hidden="true" />
        Refresh
      </button>

      <button className="planning-btn planning-btn-ghost" onClick={onReset} disabled={isLoading}>
        <X size={14} className="planning-btn-icon" aria-hidden="true" />
        Reset
      </button>
    </div>
  );
}

function ViewModeSwitch({
  mode,
  onChange,
}: {
  mode: PlanningViewMode;
  onChange: (next: PlanningViewMode) => void;
}) {
  const options: Array<{
    value: PlanningViewMode;
    label: string;
    icon: typeof LayoutGrid;
  }> = [
    { value: "global", label: "Global", icon: LayoutGrid },
    { value: "group", label: "By Groups", icon: Users },
    { value: "trainer", label: "By Trainers", icon: GraduationCap },
  ];

  return (
    <fieldset className="planning-view-switch" aria-label="Planning view mode">
      {options.map(({ value, label, icon: Icon }) => (
        <label key={value} className="planning-view-option">
          <input
            type="radio"
            name="planning-view-mode"
            value={value}
            checked={mode === value}
            onChange={() => onChange(value)}
          />
          <span className="planning-view-pill">
            <Icon size={14} className="planning-btn-icon" aria-hidden="true" />
            {label}
          </span>
        </label>
      ))}
    </fieldset>
  );
}

function StatsBar({
  sessionsByDay,
  sessionsByCourse,
}: {
  sessionsByDay: Record<string, SessionSlot[]>;
  sessionsByCourse: Record<string, SessionSlot[]>;
}) {
  if (!Object.keys(sessionsByDay).length) return null;

  return (
    <div className="planning-stats-row">
      <div className="planning-stat-card">
        <span className="planning-stat-label">Days used</span>
        <span className="planning-stat-value">{Object.keys(sessionsByDay).length}</span>
      </div>

      <div className="planning-stat-card">
        <span className="planning-stat-label">Courses</span>
        <span className="planning-stat-value">{Object.keys(sessionsByCourse).length}</span>
      </div>

      {Object.entries(sessionsByDay).map(([day, slots]) => (
        <div key={day} className="planning-stat-card">
          <span className="planning-stat-label">{day}</span>
          <span className="planning-stat-value">{slots.length} sessions</span>
        </div>
      ))}
    </div>
  );
}

export default function PlanningPage() {
  const [mode, setMode] = useState<PlanningViewMode>("global");

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
    setUserInput,
    handleRun,
    handleValidate,
    handleExport,
    handleRefresh,
    handleReset,
  } = usePlanning();

  return (
    <div className="planning-page">
      <header className="planning-header">
        <div className="planning-header-inner">
          <div className="planning-logo-mark" aria-hidden="true">
            <Sparkles size={30} />
          </div>
          <div>
            <h1 className="planning-title">Planning Agent</h1>
            <p className="planning-subtitle">AI-powered training schedule generator</p>
          </div>
        </div>
      </header>

      <main className="planning-main">
        <ConstraintInput value={userInput} onChange={setUserInput} disabled={isLoading} />

        <ActionBar
          isLoading={isLoading}
          isExporting={isExporting}
          canValidate={canValidate}
          canExport={canExport}
          onRun={handleRun}
          onValidate={handleValidate}
          onExport={handleExport}
          onReset={handleReset}
          onRefresh={handleRefresh}
        />

        <StatusBanner
          status={state.status}
          error={state.error}
          totalSessions={state.schedule.length}
        />

        {state.constraints && <ConstraintsSummary constraints={state.constraints} />}

        {hasSchedule && (
          <StatsBar sessionsByDay={sessionsByDay} sessionsByCourse={sessionsByCourse} />
        )}

        {hasSchedule && <ViewModeSwitch mode={mode} onChange={setMode} />}

        {hasSchedule && mode === "global" && (
          <PlanningTable schedule={state.schedule} mode="global" />
        )}

        {hasSchedule && mode !== "global" && (
          <GroupedPlanningView schedule={state.schedule} mode={mode} />
        )}
      </main>
    </div>
  );
}
