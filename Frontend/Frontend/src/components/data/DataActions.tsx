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
    <section className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
      <div className="flex flex-wrap gap-3 items-center">
        <button
          type="button"
          onClick={onRefresh}
          disabled={loading}
          className="px-4 py-2 rounded-md border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50"
        >
          Refresh Preview
        </button>

        {status !== 'validated' && (
          <button
            type="button"
            onClick={onValidate}
            disabled={loading}
            className="px-4 py-2 rounded-md bg-emerald-600 text-white hover:bg-emerald-700 disabled:bg-gray-300"
          >
            Validate Data
          </button>
        )}

        <button
          type="button"
          onClick={onReject}
          disabled={loading}
          className="px-4 py-2 rounded-md bg-red-600 text-white hover:bg-red-700 disabled:bg-gray-300"
        >
          Reject
        </button>

        <button
          type="button"
          onClick={onReset}
          disabled={loading}
          className="px-4 py-2 rounded-md border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50"
        >
          Reset
        </button>
      </div>
    </section>
  );
}
