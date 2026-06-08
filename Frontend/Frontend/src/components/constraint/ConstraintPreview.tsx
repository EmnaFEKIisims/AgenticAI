import { useState } from "react";

interface ConstraintPreviewProps {
  data: unknown;
}

export default function ConstraintPreview({ data }: ConstraintPreviewProps) {
  const [showJson, setShowJson] = useState(false);

  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
            Constraint Preview
          </p>
          <h3 className="mt-1 text-xl font-bold text-slate-900">JSON Debug View</h3>
        </div>

        <button
          type="button"
          onClick={() => setShowJson((current) => !current)}
          className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-100"
        >
          {showJson ? "Hide JSON" : "Show JSON"}
        </button>
      </div>

      {showJson ? (
        <pre className="mt-4 overflow-auto rounded-2xl bg-slate-950 p-4 text-sm leading-6 text-emerald-200">
          {JSON.stringify(data, null, 2)}
        </pre>
      ) : (
        <p className="mt-4 text-sm text-slate-500">
          Toggle the raw output to inspect the merged constraint payload.
        </p>
      )}
    </section>
  );
}
