// components/planning/RegenerationDialog.tsx
// Modal for requesting a new planning proposal with custom modifications.

import { useState } from "react";

interface RegenerationDialogProps {
  attempt:       number;
  regenerating:  boolean;
  onRegenerate:  (userConstraints: string) => void;
  onCancel:      () => void;
}

export default function RegenerationDialog({
  attempt, regenerating, onRegenerate, onCancel,
}: RegenerationDialogProps) {
  const [constraints, setConstraints] = useState("");

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
      <div className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-6 shadow-2xl space-y-4">

        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            New Proposal — Attempt #{attempt}
          </p>
          <h3 className="mt-1 text-lg font-bold text-slate-900">
            Request a different planning
          </h3>
          <p className="mt-1 text-sm text-slate-600">
            Optionally describe what you want changed. Leave empty to generate a completely different proposal.
          </p>
        </div>

        <div>
          <label className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Modification request (optional)
          </label>
          <textarea
            value={constraints}
            onChange={e => setConstraints(e.target.value)}
            placeholder={
              "e.g. Move ML to Wednesday morning.\n" +
              "Reduce Ahmed's load on Thursdays.\n" +
              "No sessions after 16:00 on Fridays."
            }
            rows={5}
            className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-800 outline-none focus:border-slate-400 resize-none"
          />
        </div>

        <div className="flex gap-3 pt-1">
          <button
            onClick={() => onRegenerate(constraints)}
            disabled={regenerating}
            className="flex-1 rounded-xl bg-violet-600 py-2.5 text-sm font-semibold text-white hover:bg-violet-700 disabled:opacity-60 transition"
          >
            {regenerating ? (
              <span className="flex items-center justify-center gap-2">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                Generating…
              </span>
            ) : "🔄 Generate new proposal"}
          </button>
          <button onClick={onCancel} disabled={regenerating}
            className="flex-1 rounded-xl border border-slate-200 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50">
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}