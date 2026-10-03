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
    <div className="crud-data-table-wrap">
      <table className="crud-data-table">
        <thead>
          <tr>
            {columns.map(col => (
              <th key={String(col.key)}
                className="crud-th"
                style={{ width: col.width }}>
                {col.label}
              </th>
            ))}
            {(onEdit || onDelete) && (
              <th className="crud-th crud-actions-heading">
                Actions
              </th>
            )}
          </tr>
        </thead>
        <tbody>
          {data.map(row => (
            <tr key={String(row[rowKey])}
              className="crud-tr group">
              {columns.map(col => (
                <td key={String(col.key)} className="crud-td">
                  {col.render
                    ? col.render(row)
                    : String(row[col.key as keyof T] ?? "—")}
                </td>
              ))}
              {(onEdit || onDelete) && (
                <td className="crud-td crud-actions-cell">
                  <div className="crud-row-actions">
                    {onEdit && (
                      <button onClick={() => onEdit(row)}
                        className="crud-edit-button">
                        <Pencil className="h-3 w-3" aria-hidden="true" />
                        Edit
                      </button>
                    )}
                    {onDelete && (
                      <button onClick={() => onDelete(row)}
                        className="crud-delete-button">
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