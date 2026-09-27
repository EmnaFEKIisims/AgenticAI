import { RefreshCw, CheckCircle2, XCircle, RotateCcw } from 'lucide-react';

interface DataActionsProps {
  status: 'idle' | 'uploading' | 'processing' | 'preview' | 'validated' | 'rejected';
  onValidate: () => void;
  onReject: () => void;
  onReset: () => void;
  onRefresh: () => void;
  loading: boolean;
}

export default function DataActions({
  status,
  onValidate,
  onReject,
  onReset,
  onRefresh,
  loading,
}: DataActionsProps) {
  return (
    <section className="data-actions-bar">
      <div className="data-actions-label"><span className="data-actions-pulse" /> Review controls</div>
      <div className="data-actions-buttons">
        <button
          type="button"
          onClick={onRefresh}
          disabled={loading}
          className="data-secondary-button"
        >
          <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" />
          Refresh preview
        </button>

        <div className="data-actions-spacer" />

        {status !== 'validated' && (
          <button
            type="button"
            onClick={onValidate}
            disabled={loading}
            className="data-approve-button"
          >
            <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
            Validate data
          </button>
        )}

        <button
          type="button"
          onClick={onReject}
          disabled={loading}
          className="data-danger-button"
        >
          <XCircle className="h-3.5 w-3.5" aria-hidden="true" />
          Reject
        </button>

        <button
          type="button"
          onClick={onReset}
          disabled={loading}
          className="data-secondary-button"
        >
          <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
          Reset
        </button>
      </div>
    </section>
  );
}