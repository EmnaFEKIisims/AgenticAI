// src/components/crud/DeleteDialog.tsx
interface Props {
  name:      string;
  onConfirm: () => void;
  onCancel:  () => void;
  loading?:  boolean;
}

export default function DeleteDialog({ name, onConfirm, onCancel, loading }: Props) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="w-full max-w-sm rounded-3xl border border-slate-200 bg-white p-6 shadow-2xl space-y-4">
        <div className="text-center space-y-2">
          <p className="text-3xl">🗑️</p>
          <h3 className="text-base font-bold text-slate-900">Delete confirmation</h3>
          <p className="text-sm text-slate-600">
            Are you sure you want to delete <span className="font-semibold">"{name}"</span>?
            <br/>
            <span className="text-xs text-slate-400">
              If linked to an active planning, it will be deactivated instead.
            </span>
          </p>
        </div>
        <div className="flex gap-3">
          <button onClick={onCancel}
            className="flex-1 rounded-xl border border-slate-200 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition">
            Cancel
          </button>
          <button onClick={onConfirm} disabled={loading}
            className="flex-1 rounded-xl bg-rose-600 py-2 text-sm font-semibold text-white hover:bg-rose-700 disabled:opacity-60 transition">
            {loading ? "Deleting…" : "Delete"}
          </button>
        </div>
      </div>
    </div>
  );
}