import { useEffect, useMemo, useState } from 'react';
import { PreviewRecord, ValidationIssue } from '../../types/dataManager';

interface DataPreviewTableProps {
  data: PreviewRecord[];
  issues: ValidationIssue[];
  onDataUpdate: (updatedData: PreviewRecord[]) => void;
  loading: boolean;
}

export default function DataPreviewTable({
  data,
  issues,
  onDataUpdate,
  loading,
}: DataPreviewTableProps) {
  const [editableData, setEditableData] = useState<PreviewRecord[]>(data);

  useEffect(() => {
    setEditableData(data);
  }, [data]);

  const columns = useMemo(() => {
    const keySet = new Set<string>();
    data.forEach((record) => {
      Object.keys(record).forEach((key) => keySet.add(key));
    });
    return Array.from(keySet);
  }, [data]);

  const handleCellChange = (rowIndex: number, key: string, value: string) => {
    setEditableData((prev) => {
      const next = [...prev];
      next[rowIndex] = {
        ...next[rowIndex],
        [key]: value,
      };
      return next;
    });
  };

  const handleSave = () => {
    onDataUpdate(editableData);
  };

  if (!data.length) {
    return (
      <section className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        <p className="text-gray-600">No preview data available yet.</p>
      </section>
    );
  }

  return (
    <section className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-xl font-semibold text-gray-900">Preview Data</h2>
        <button
          type="button"
          onClick={handleSave}
          disabled={loading}
          className="px-4 py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700 disabled:bg-gray-300"
        >
          Save Corrections
        </button>
      </div>

      {issues.length > 0 && (
        <div className="border border-amber-200 bg-amber-50 rounded-lg p-3">
          <h3 className="font-medium text-amber-800 mb-2">Validation issues: {issues.length}</h3>
          <ul className="text-sm text-amber-700 list-disc list-inside space-y-1 max-h-40 overflow-auto">
            {issues.map((issue, index) => (
              <li key={`${issue.entity_type}-${index}`}>
                {issue.entity_type}: {issue.issues.join(', ')}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="overflow-auto border border-gray-200 rounded-lg">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              {columns.map((column) => (
                <th key={column} className="text-left p-2 border-b border-gray-200 font-semibold text-gray-700 whitespace-nowrap">
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {editableData.map((row, rowIndex) => (
              <tr key={rowIndex} className="odd:bg-white even:bg-gray-50">
                {columns.map((column) => {
                  const value = row[column];
                  return (
                    <td key={`${column}-${rowIndex}`} className="p-2 border-b border-gray-100 align-top min-w-40">
                      <input
                        type="text"
                        value={value == null ? '' : String(value)}
                        onChange={(event) => handleCellChange(rowIndex, column, event.target.value)}
                        className="w-full border border-gray-200 rounded px-2 py-1"
                      />
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
