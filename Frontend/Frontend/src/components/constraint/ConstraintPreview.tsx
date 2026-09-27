import { useState } from "react";
import { Braces, ChevronDown, ChevronUp } from "lucide-react";

interface ConstraintPreviewProps {
  data: unknown;
}

export default function ConstraintPreview({ data }: ConstraintPreviewProps) {
  const [showJson, setShowJson] = useState(false);

  return (
    <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <header className="flex items-center gap-4 border-b border-slate-100 bg-linear-to-br from-slate-50 via-white to-white px-6 py-6 sm:px-8">
        <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-slate-900 text-white shadow-sm">
          <Braces className="h-5 w-5" aria-hidden="true" />
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="text-lg font-semibold tracking-tight text-slate-900">
            Payload preview
          </h3>
          <p className="mt-0.5 text-sm text-slate-500">
            Raw merged constraint payload sent to the agent.
          </p>
        </div>

        <button
          type="button"
          onClick={() => setShowJson((current) => !current)}
          className="shrink-0 inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
        >
          {showJson ? (
            <>
              <ChevronUp className="h-3.5 w-3.5" aria-hidden="true" />
              Hide
            </>
          ) : (
            <>
              <ChevronDown className="h-3.5 w-3.5" aria-hidden="true" />
              Show
            </>
          )}
        </button>
      </header>

      <div className="bg-slate-50/40 p-6 sm:p-8">
        {showJson ? (
          <pre className="max-h-96 overflow-auto rounded-2xl border border-slate-800 bg-slate-950 p-4 text-xs leading-6 text-emerald-200 shadow-inner">
            {JSON.stringify(data, null, 2)}
          </pre>
        ) : (
          <p className="text-sm text-slate-500">
            Toggle to inspect the raw merged constraint payload.
          </p>
        )}
      </div>
    </section>
  );
}