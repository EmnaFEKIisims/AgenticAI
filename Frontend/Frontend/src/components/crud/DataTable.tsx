// src/components/crud/DataTable.tsx
// Generic table — reused by ALL entity pages.
// Pass columns definition + data, it handles rendering.

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
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-200 bg-slate-50">
            {columns.map(col => (
              <th key={String(col.key)}
                className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500"
                style={{ width: col.width }}>
                {col.label}
              </th>
            ))}
            {(onEdit || onDelete) && (
              <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-slate-500 w-28">
                Actions
              </th>
            )}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {data.map(row => (
            <tr key={String(row[rowKey])} className="hover:bg-slate-50 transition-colors">
              {columns.map(col => (
                <td key={String(col.key)} className="px-4 py-3 text-slate-700">
                  {col.render
                    ? col.render(row)
                    : String(row[col.key as keyof T] ?? "—")}
                </td>
              ))}
              {(onEdit || onDelete) && (
                <td className="px-4 py-3 text-right">
                  <div className="flex justify-end gap-2">
                    {onEdit && (
                      <button onClick={() => onEdit(row)}
                        className="rounded-lg border border-slate-200 px-3 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100 transition">
                        ✏️ Edit
                      </button>
                    )}
                    {onDelete && (
                      <button onClick={() => onDelete(row)}
                        className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-1 text-xs font-medium text-rose-700 hover:bg-rose-100 transition">
                        🗑 Delete
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