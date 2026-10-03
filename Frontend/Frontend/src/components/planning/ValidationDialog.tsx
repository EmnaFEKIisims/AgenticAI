// components/planning/ValidationDialog.tsx
// Modal asking for reject reason or modification request.

import { useState } from "react";

interface ValidationDialogProps {
  mode:      "reject" | "modify";
  loading:   boolean;
  onConfirm: (text: string) => void;
  onCancel:  () => void;
}

export default function ValidationDialog({ mode, loading, onConfirm, onCancel }: ValidationDialogProps) {
  const [text, setText] = useState("");

  const isReject = mode === "reject";
  const title    = isReject ? "Reject this planning?" : "Request a modification";
  const label    = isReject ? "Reason for rejection (optional)" : "Describe the modification";
  const ph       = isReject
    ? "e.g. Too many sessions on Monday, not enough break time..."
    : "e.g. Move ML to Wednesday morning. Reduce Thursday load.";
  const btnLabel = isReject ? "Confirm rejection" : "Apply & regenerate";
  const btnClass = isReject
    ? "bg-rose-600 hover:bg-rose-700"
    : "bg-violet-600 hover:bg-violet-700";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
      <div className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-6 shadow-2xl space-y-4">

        <h3 className="text-lg font-bold text-slate-900">{title}</h3>

        <div>
          <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            {label}
          </label>
          <textarea
            value={text}
            onChange={e => setText(e.target.value)}
            placeholder={ph}
            rows={4}
            className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-800 outline-none focus:border-slate-400 resize-none"
          />
        </div>

        <div className="flex gap-3 pt-1">
          <button onClick={() => onConfirm(text)} disabled={loading}
            className={`flex-1 rounded-xl py-2.5 text-sm font-semibold text-white transition ${btnClass} disabled:opacity-60`}>
            {loading ? "Processing…" : btnLabel}
          </button>
          <button onClick={onCancel} disabled={loading}
            className="flex-1 rounded-xl border border-slate-200 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50">
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}