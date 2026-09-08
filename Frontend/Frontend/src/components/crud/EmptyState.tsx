// src/components/crud/EmptyState.tsx
interface Props { message?: string; onAdd?: () => void; }
export function EmptyState({ message = "No items found.", onAdd }: Props) {
  return (
    <div className="py-16 text-center space-y-3">
      <p className="text-4xl">📭</p>
      <p className="text-sm font-semibold text-slate-600">{message}</p>
      {onAdd && (
        <button onClick={onAdd}
          className="rounded-xl bg-slate-900 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-800">
          + Add first item
        </button>
      )}
    </div>
  );
}

// src/components/crud/LoadingState.tsx
export function LoadingState({ text = "Loading…" }: { text?: string }) {
  return (
    <div className="py-16 text-center space-y-3">
      <div className="w-8 h-8 border-2 border-slate-300 border-t-slate-900 rounded-full animate-spin mx-auto" />
      <p className="text-sm text-slate-500">{text}</p>
    </div>
  );
}

// src/components/crud/Pagination.tsx
interface PaginationProps {
  page:      number;
  total:     number;
  pageSize:  number;
  onChange:  (p: number) => void;
}
export function Pagination({ page, total, pageSize, onChange }: PaginationProps) {
  const totalPages = Math.ceil(total / pageSize);
  if (totalPages <= 1) return null;
  return (
    <div className="flex items-center justify-between px-4 py-3 border-t border-slate-100">
      <p className="text-xs text-slate-500">
        Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, total)} of {total}
      </p>
      <div className="flex gap-1">
        <button onClick={() => onChange(page - 1)} disabled={page === 1}
          className="rounded-lg border border-slate-200 px-3 py-1 text-xs disabled:opacity-40 hover:bg-slate-50">
          ← Prev
        </button>
        {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
          const p = Math.max(1, page - 2) + i;
          if (p > totalPages) return null;
          return (
            <button key={p} onClick={() => onChange(p)}
              className={`rounded-lg border px-3 py-1 text-xs transition ${
                p === page ? "border-slate-900 bg-slate-900 text-white" : "border-slate-200 hover:bg-slate-50"
              }`}>
              {p}
            </button>
          );
        })}
        <button onClick={() => onChange(page + 1)} disabled={page === totalPages}
          className="rounded-lg border border-slate-200 px-3 py-1 text-xs disabled:opacity-40 hover:bg-slate-50">
          Next →
        </button>
      </div>
    </div>
  );
}