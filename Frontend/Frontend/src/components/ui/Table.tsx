import type React from "react";

export interface TableColumn<T> {
  key: keyof T;
  label: string;
}

interface TableProps<T> {
  columns: Array<TableColumn<T>>;
  rows: T[];
  tableStyle?: React.CSSProperties;
  tableClassName?: string;
  thStyle?: React.CSSProperties;
  thClassName?: string;
  tdStyle?: React.CSSProperties;
  tdClassName?: string;
  getRowKey: (row: T, index: number) => React.Key;
  getRowStyle?: (row: T, index: number) => React.CSSProperties;
  getRowClassName?: (row: T, index: number) => string;
  renderCell?: (row: T, column: TableColumn<T>, index: number) => React.ReactNode;
}

export default function Table<T>({
  columns,
  rows,
  tableStyle,
  tableClassName,
  thStyle,
  thClassName,
  tdStyle,
  tdClassName,
  getRowKey,
  getRowStyle,
  getRowClassName,
  renderCell,
}: TableProps<T>) {
  return (
    <table style={tableStyle} className={tableClassName}>
      <thead>
        <tr>
          {columns.map((column) => (
            <th key={String(column.key)} style={thStyle} className={thClassName}>
              {column.label}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, rowIndex) => (
          <tr
            key={getRowKey(row, rowIndex)}
            style={getRowStyle?.(row, rowIndex)}
            className={getRowClassName?.(row, rowIndex)}
          >
            {columns.map((column) => (
              <td key={String(column.key)} style={tdStyle} className={tdClassName}>
                {renderCell
                  ? renderCell(row, column, rowIndex)
                  : String(row[column.key])}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
