import Input from "../ui/Input";

interface UserConstraintInputProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export default function UserConstraintInput({ value, onChange, disabled = false }: UserConstraintInputProps) {
  return (
    <section className="rounded-2xl border border-sky-200 bg-sky-50/70 p-5 shadow-sm">
      <div className="mb-3">
        <h3 className="text-sm font-semibold uppercase tracking-[0.24em] text-sky-900">
          Scheduling Constraints
        </h3>
        <p className="mt-1 text-sm text-sky-900/70">
          User-defined availability, exclusions, and operational constraints.
        </p>
      </div>

      <Input
        multiline
        rows={5}
        value={value}
        onChange={onChange}
        disabled={disabled}
        placeholder={"No sessions on Friday\nAhmed available Monday\nNo evening sessions"}
        className="min-h-32 w-full rounded-xl border border-sky-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200 disabled:cursor-not-allowed disabled:bg-slate-100"
      />
    </section>
  );
}
