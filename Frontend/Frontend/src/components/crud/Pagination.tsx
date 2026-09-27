// src/components/crud/Pagination.tsx
import { ChevronLeft, ChevronRight } from "lucide-react";

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
    <div className="flex items-center justify-between gap-4 border-t border-slate-100 px-5 py-3.5">
      <p className="text-xs text-slate-500">
        Showing <span className="font-medium text-slate-700">{(page - 1) * pageSize + 1}</span>
        –<span className="font-medium text-slate-700">{Math.min(page * pageSize, total)}</span>
        {" "}of <span className="font-medium text-slate-700">{total}</span>
      </p>

      <div className="flex items-center gap-1">
        <button onClick={() => onChange(page - 1)} disabled={page === 1}
          className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-600 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40">
          <ChevronLeft className="h-3.5 w-3.5" aria-hidden="true" />
        </button>

        {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
          const p = Math.max(1, page - 2) + i;
          if (p > totalPages) return null;
          return (
            <button key={p} onClick={() => onChange(p)}
              className={`h-8 min-w-8 rounded-lg border px-3 text-xs font-semibold transition ${
                p === page
                  ? "border-slate-900 bg-slate-900 text-white shadow-sm"
                  : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
              }`}>
              {p}
            </button>
          );
        })}

        <button onClick={() => onChange(page + 1)} disabled={page === totalPages}
          className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-600 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40">
          <ChevronRight className="h-3.5 w-3.5" aria-hidden="true" />
        </button>
      </div>
    </div>
  );
}