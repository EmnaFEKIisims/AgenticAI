import { AlertTriangle, Trash2 } from "lucide-react";

interface Props {
  name:      string;
  onConfirm: () => void;
  onCancel:  () => void;
  loading?:  boolean;
}

export default function DeleteDialog({ name, onConfirm, onCancel, loading }: Props) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-sm">
      <div className="w-full max-w-sm overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-2xl">
        {/* Header */}
        <div className="flex flex-col items-center gap-3 border-b border-slate-100 bg-linear-to-b from-rose-50/60 to-white px-6 pt-6 pb-5 text-center">
          <span className="flex h-14 w-14 items-center justify-center rounded-2xl border border-rose-100 bg-white text-rose-600 shadow-sm">
            <Trash2 className="h-6 w-6" aria-hidden="true" />
          </span>
          <div className="space-y-1">
            <h3 className="text-base font-semibold tracking-tight text-slate-900">
              Delete confirmation
            </h3>
            <p className="text-sm text-slate-600">
              Are you sure you want to delete{" "}
              <span className="font-semibold text-slate-900">"{name}"</span>?
            </p>
          </div>
        </div>

        {/* Notice */}
        <div className="mx-6 mt-4 flex items-start gap-2.5 rounded-xl border border-amber-100 bg-amber-50/60 px-3.5 py-3">
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-600" aria-hidden="true" />
          <p className="text-xs leading-relaxed text-amber-900">
            If linked to an active planning, it will be deactivated instead.
          </p>
        </div>

        {/* Actions */}
        <div className="flex gap-3 p-6 pt-5">
          <button onClick={onCancel}
            className="flex-1 rounded-xl border border-slate-200 bg-white py-2.5 text-sm font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50">
            Cancel
          </button>
          <button onClick={onConfirm} disabled={loading}
            className="flex-1 rounded-xl bg-rose-600 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-rose-700 hover:shadow disabled:cursor-not-allowed disabled:opacity-60">
            {loading ? "Deleting…" : "Delete"}
          </button>
        </div>
      </div>
    </div>
  );
}