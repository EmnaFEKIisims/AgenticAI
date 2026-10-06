import { RefreshCw, Sparkles, SlidersHorizontal, Wand2 } from "lucide-react";
import type { ConstraintFormValue } from "../../types/constraintTypes";
import PedagogicalInput from "./PedagogicalInput";
import UserConstraintInput from "./UserConstraintInput";

interface ConstraintFormProps {
  value: ConstraintFormValue;
  onChange: (value: ConstraintFormValue) => void;
  onGenerate: () => void;
  onReset: () => void;
  disabled?: boolean;
  loading?: boolean;
}

export default function ConstraintForm({
  value,
  onChange,
  onGenerate,
  onReset,
  disabled = false,
  loading = false,
}: ConstraintFormProps) {
  const isDisabled = disabled || loading;

  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      {/* Card header */}
      <header className="relative border-b border-slate-100 bg-linear-to-br from-slate-50 via-white to-white px-6 py-6 sm:px-8">
        <div className="flex items-start gap-4">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-blue-100 text-blue-700 shadow-sm">
            <SlidersHorizontal className="h-5 w-5" aria-hidden="true" />
          </span>
          <div className="min-w-0 flex-1">
            <h2 className="text-lg font-semibold tracking-tight text-slate-900">
              Configure your planning
            </h2>
            <p className="mt-0.5 text-sm text-slate-500">
              Fill in one or both fields, then generate your schedule.
            </p>
          </div>
          <span className="hidden shrink-0 items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600 sm:inline-flex">
            <Wand2 className="h-3 w-3 text-slate-500" aria-hidden="true" />
            AI-powered
          </span>
        </div>
      </header>

      {/* Inputs */}
      <div className="grid gap-5 bg-slate-50/40 p-6 sm:grid-cols-2 sm:p-8">
        <PedagogicalInput
          value={value.pedagogicalText}
          onChange={(pedagogicalText) => onChange({ ...value, pedagogicalText })}
          disabled={isDisabled}
        />
        <UserConstraintInput
          value={value.userText}
          onChange={(userText) => onChange({ ...value, userText })}
          disabled={isDisabled}
        />
      </div>

      {/* Actions */}
      <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 bg-white px-6 py-5 sm:px-8">
        <p className="text-xs text-slate-500">
          Both fields are optional — ISO rules are always applied.
        </p>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onReset}
            disabled={isDisabled}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <RefreshCw size={15} aria-hidden="true" />
            Reset
          </button>

          <button
            type="button"
            onClick={onGenerate}
            disabled={isDisabled}
            className="inline-flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-100 px-5 py-2.5 text-sm font-semibold text-rose-700 shadow-sm transition hover:border-rose-300 hover:bg-rose-200 hover:shadow disabled:cursor-not-allowed disabled:opacity-60"
          >
            <Sparkles size={15} aria-hidden="true" />
            {loading ? "Generating..." : "Generate planning"}
          </button>
        </div>
      </footer>
    </div>
  );
}