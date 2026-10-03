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
    <div className="crud-pagination">
      <p>
        Showing <strong>{(page - 1) * pageSize + 1}</strong>
        –<strong>{Math.min(page * pageSize, total)}</strong>
        {" "}of <strong>{total}</strong>
      </p>

      <div className="crud-pagination-buttons">
        <button onClick={() => onChange(page - 1)} disabled={page === 1}
          className="crud-page-button icon-button">
          <ChevronLeft className="h-3.5 w-3.5" aria-hidden="true" />
        </button>

        {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
          const p = Math.max(1, page - 2) + i;
          if (p > totalPages) return null;
          return (
            <button key={p} onClick={() => onChange(p)}
              className={`crud-page-button ${
                p === page
                  ? "is-current"
                  : ""
              }`}>
              {p}
            </button>
          );
        })}

        <button onClick={() => onChange(page + 1)} disabled={page === totalPages}
          className="crud-page-button icon-button">
          <ChevronRight className="h-3.5 w-3.5" aria-hidden="true" />
        </button>
      </div>
    </div>
  );
}