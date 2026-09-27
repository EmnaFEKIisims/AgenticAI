import { useEffect, useMemo, useState } from 'react';
import { Table2, AlertTriangle, Save, Database } from 'lucide-react';
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
      <section className="data-panel data-preview-panel">
        <div className="data-empty-state">
          <span className="data-empty-icon">
            <Database className="h-6 w-6" aria-hidden="true" />
          </span>
          <p>
            No preview data available yet
          </p>
          <p>
            Upload a file to see a preview here.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="data-panel data-preview-panel">
      {/* Header */}
      <header className="data-panel-header">
        <div className="flex items-center gap-4">
          <span className="data-icon-tile data-icon-tile-blue">
            <Table2 className="h-5 w-5" aria-hidden="true" />
          </span>
          <div className="min-w-0">
            <h2>
              Preview data
            </h2>
            <p>
              Edit any cell directly, then save your corrections.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={handleSave}
          disabled={loading}
          className="data-primary-button"
        >
          <Save className="h-4 w-4" aria-hidden="true" />
          Save corrections
        </button>
      </header>

      <div className="data-panel-body">
        {/* Validation issues */}
        {issues.length > 0 && (
          <div className="data-issues-box">
            <div className="data-issues-header">
              <span className="data-issues-icon">
                <AlertTriangle className="h-3.5 w-3.5" aria-hidden="true" />
              </span>
              <h3>
                Validation issues
              </h3>
              <span className="data-issues-count">
                {issues.length}
              </span>
            </div>
            <ul className="data-issues-list">
              {issues.map((issue, index) => (
                <li
                  key={`${issue.entity_type}-${index}`}
                  className="data-issue-row"
                >
                  <span className="data-issue-dot" />
                  <span>
                    <span className="data-issue-entity">
                      {issue.entity_type}
                    </span>
                    <span className="data-issue-copy">
                      {' — '}
                      {issue.issues.join(', ')}
                    </span>
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Table */}
        <div className="data-table-wrap">
          <div className="overflow-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="data-table-head">
                  {columns.map((column) => (
                    <th
                      key={column}
                      className="data-table-heading"
                    >
                      {column}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="data-table-body">
                {editableData.map((row, rowIndex) => (
                  <tr
                    key={rowIndex}
                    className="data-table-row"
                  >
                    {columns.map((column) => {
                      const value = row[column];
                      return (
                        <td
                          key={`${column}-${rowIndex}`}
                          className="data-table-cell"
                        >
                          <input
                            type="text"
                            value={value == null ? '' : String(value)}
                            onChange={(event) =>
                              handleCellChange(rowIndex, column, event.target.value)
                            }
                            className="data-table-input"
                          />
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>
  );
}