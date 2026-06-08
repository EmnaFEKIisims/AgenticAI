import type { ConstraintSummaryData } from "../../types/constraintTypes";

interface ConstraintSummaryProps {
  data: ConstraintSummaryData;
}

function Section({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <h4 className="text-sm font-semibold uppercase tracking-[0.22em] text-slate-500">{title}</h4>
      <div className="mt-3 space-y-2 text-sm text-slate-800">
        {items.length ? (
          items.map((item) => <div key={item}>{item}</div>)
        ) : (
          <p className="text-slate-400">No data provided.</p>
        )}
      </div>
    </div>
  );
}

export default function ConstraintSummary({ data }: ConstraintSummaryProps) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-5">
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
          Merged Constraints
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Section title="Forbidden Days" items={data.forbiddenDays} />

        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <h4 className="text-sm font-semibold uppercase tracking-[0.22em] text-slate-500">
            Trainer Availability
          </h4>
          <div className="mt-3 space-y-3 text-sm text-slate-800">
            {data.trainerAvailability.length ? (
              data.trainerAvailability.map((entry) => (
                <div key={entry.trainer} className="rounded-xl bg-white px-3 py-2 shadow-sm">
                  <span className="font-semibold text-slate-900">{entry.trainer}</span>
                  <span className="mx-2 text-slate-400">→</span>
                  <span>{entry.availability.length ? entry.availability.join(", ") : "No availability provided"}</span>
                </div>
              ))
            ) : (
              <p className="text-slate-400">No trainer availability.</p>
            )}
          </div>
        </div>

        <Section title="Planning Parameters" items={data.planningParameters.map((parameter) => `${parameter.label} : ${parameter.value}`)} />

        <Section title="Pedagogical Rules" items={data.pedagogicalRules.map((rule) => `• ${rule}`)} />
      </div>
    </section>
  );
}
