// src/components/crud/DataTable.tsx
// Generic table — reused by ALL entity pages.
// Pass columns definition + data, it handles rendering.

import { Pencil, Trash2 } from "lucide-react";

export interface Column<T> {
  key:      keyof T | string;
  label:    string;
  width?:   string;
  render?:  (row: T) => React.ReactNode;
}

interface Props<T> {
  columns:    Column<T>[];
  data:       T[];
  onEdit?:    (row: T) => void;
  onDelete?:  (row: T) => void;
  rowKey:     keyof T;
}

export default function DataTable<T>({ columns, data, onEdit, onDelete, rowKey }: Props<T>) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-100">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-100 bg-linear-to-b from-slate-50 to-slate-50/50">
            {columns.map(col => (
              <th key={String(col.key)}
                className="px-5 py-3.5 text-left text-[11px] font-semibold uppercase tracking-wider text-slate-500"
                style={{ width: col.width }}>
                {col.label}
              </th>
            ))}
            {(onEdit || onDelete) && (
              <th className="w-28 px-5 py-3.5 text-right text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                Actions
              </th>
            )}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-50">
          {data.map(row => (
            <tr key={String(row[rowKey])}
              className="group bg-white transition-colors hover:bg-slate-50/60">
              {columns.map(col => (
                <td key={String(col.key)} className="px-5 py-3.5 text-slate-700">
                  {col.render
                    ? col.render(row)
                    : String(row[col.key as keyof T] ?? "—")}
                </td>
              ))}
              {(onEdit || onDelete) && (
                <td className="px-5 py-3.5 text-right">
                  <div className="flex justify-end gap-1.5 opacity-70 transition-opacity group-hover:opacity-100">
                    {onEdit && (
                      <button onClick={() => onEdit(row)}
                        className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-50 hover:shadow-sm">
                        <Pencil className="h-3 w-3" aria-hidden="true" />
                        Edit
                      </button>
                    )}
                    {onDelete && (
                      <button onClick={() => onDelete(row)}
                        className="inline-flex items-center gap-1.5 rounded-lg border border-rose-100 bg-rose-50/60 px-2.5 py-1.5 text-xs font-medium text-rose-700 transition hover:border-rose-200 hover:bg-rose-50 hover:shadow-sm">
                        <Trash2 className="h-3 w-3" aria-hidden="true" />
                        Delete
                      </button>
                    )}
                  </div>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}