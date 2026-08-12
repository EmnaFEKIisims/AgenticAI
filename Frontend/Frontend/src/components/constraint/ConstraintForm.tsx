import { RefreshCw, Sparkles } from "lucide-react";
import Button from "../ui/Button";
import Card from "../ui/Card";
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
  const updatePedagogicalText = (pedagogicalText: string) => {
    onChange({ ...value, pedagogicalText });
  };

  const updateUserText = (userText: string) => {
    onChange({ ...value, userText });
  };

  const isDisabled = disabled || loading;

  return (
    <Card className="rounded-3xl border border-slate-200 bg-white p-6 shadow-lg shadow-slate-200/50">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Constraint Form</h2>
          <p className="mt-1 text-sm text-slate-500">
            Combine pedagogical and user constraints before running the agent.
          </p>
        </div>
        <div className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
          ISO + pedagogical + user
        </div>
      </div>

      <div className="grid gap-4">
        <PedagogicalInput
          value={value.pedagogicalText}
          onChange={updatePedagogicalText}
          disabled={isDisabled}
        />

        <UserConstraintInput
          value={value.userText}
          onChange={updateUserText}
          disabled={isDisabled}
        />
      </div>

      <div className="mt-6 flex flex-wrap gap-3">
        <Button
          type="button"
          onClick={onGenerate}
          disabled={isDisabled}
          className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <Sparkles size={16} aria-hidden="true" />
          {loading ? "Generating planning..." : "Generate Planning"}
        </Button>

        <Button
          type="button"
          onClick={onReset}
          disabled={isDisabled}
          className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <RefreshCw size={16} aria-hidden="true" />
          Reset
        </Button>
      </div>
    </Card>
  );
}
