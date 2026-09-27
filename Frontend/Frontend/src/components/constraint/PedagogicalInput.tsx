import { BookOpen, Sparkles } from "lucide-react";
import Input from "../ui/Input";

interface PedagogicalInputProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export default function PedagogicalInput({ value, onChange, disabled = false }: PedagogicalInputProps) {
  return (
    <div className="rounded-2xl border border-emerald-100 bg-linear-to-br from-emerald-50/70 via-white to-white p-5 transition-shadow hover:shadow-sm">
      <header className="mb-4 flex items-start gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-emerald-100 bg-white text-emerald-600 shadow-sm">
          <BookOpen className="h-4 w-4" aria-hidden="true" />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold tracking-tight text-slate-900">
              Pedagogical constraints
            </h3>
            <span className="rounded-full bg-emerald-100/70 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-emerald-700">
              Learning
            </span>
          </div>
          <p className="mt-0.5 text-xs text-slate-500">
            How the training should be structured for learners.
          </p>
        </div>
      </header>

      <Input
        multiline
        rows={5}
        value={value}
        onChange={onChange}
        disabled={disabled}
        placeholder={"Start with fundamentals\nAvoid cognitive overload\nBalance theory and practice"}
        className="w-full rounded-xl border border-emerald-100 bg-white px-4 py-3 text-sm text-slate-800 placeholder:text-slate-400 outline-none transition focus:border-emerald-300 focus:ring-2 focus:ring-emerald-100 disabled:cursor-not-allowed disabled:bg-slate-50"
      />

      <div className="mt-3 flex items-center gap-1.5 text-xs text-emerald-700/70">
        <Sparkles className="h-3 w-3" aria-hidden="true" />
        <span>Tip: describe the ideal learning progression.</span>
      </div>
    </div>
  );
}