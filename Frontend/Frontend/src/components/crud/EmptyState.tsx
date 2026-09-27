// src/components/crud/EmptyState.tsx
import { Inbox, Plus } from "lucide-react";

interface Props { message?: string; onAdd?: () => void; }

export function EmptyState({ message = "No items found.", onAdd }: Props) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-20 text-center">
      <span className="flex h-14 w-14 items-center justify-center rounded-2xl border border-slate-100 bg-linear-to-br from-slate-50 to-white text-slate-400 shadow-sm">
        <Inbox className="h-6 w-6" aria-hidden="true" />
      </span>
      <div className="space-y-1">
        <p className="text-sm font-semibold text-slate-700">{message}</p>
        <p className="text-xs text-slate-400">
          There is nothing to display here yet.
        </p>
      </div>
      {onAdd && (
        <button onClick={onAdd}
          className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-slate-800 hover:shadow">
          <Plus className="h-3.5 w-3.5" aria-hidden="true" />
          Add first item
        </button>
      )}
    </div>
  );
}
