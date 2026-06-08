import Input from "../ui/Input";

interface PedagogicalInputProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export default function PedagogicalInput({ value, onChange, disabled = false }: PedagogicalInputProps) {
  return (
    <section className="rounded-2xl border border-emerald-200 bg-emerald-50/70 p-5 shadow-sm">
      <div className="mb-3">
        <h3 className="text-sm font-semibold uppercase tracking-[0.24em] text-emerald-900">
          Pedagogical Constraints
        </h3>
        <p className="mt-1 text-sm text-emerald-900/70">
          Rules linked to learning flow, sequence, and instructional quality.
        </p>
      </div>

      <Input
        multiline
        rows={5}
        value={value}
        onChange={onChange}
        disabled={disabled}
        placeholder={"Start with fundamentals\nAvoid cognitive overload\nBalance theory and practice"}
        className="min-h-32 w-full rounded-xl border border-emerald-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-200 disabled:cursor-not-allowed disabled:bg-slate-100"
      />
    </section>
  );
}
