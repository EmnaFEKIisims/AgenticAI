interface DataStatusProps {
  status: 'idle' | 'uploading' | 'processing' | 'preview' | 'validated' | 'rejected';
  loading: boolean;
  error: string | null;
  filename: string;
}

const STATUS_COPY: Record<DataStatusProps['status'], { title: string; tone: string }> = {
  idle: {
    title: 'Waiting for file upload',
    tone: 'bg-gray-50 border-gray-200 text-gray-700',
  },
  uploading: {
    title: 'Uploading file...',
    tone: 'bg-blue-50 border-blue-200 text-blue-700',
  },
  processing: {
    title: 'Processing records...',
    tone: 'bg-amber-50 border-amber-200 text-amber-800',
  },
  preview: {
    title: 'Preview ready for review',
    tone: 'bg-sky-50 border-sky-200 text-sky-800',
  },
  validated: {
    title: 'Data validated and accepted',
    tone: 'bg-emerald-50 border-emerald-200 text-emerald-800',
  },
  rejected: {
    title: 'Upload rejected',
    tone: 'bg-red-50 border-red-200 text-red-800',
  },
};

export default function DataStatus({ status, loading, error, filename }: DataStatusProps) {
  if (error) {
    return (
      <section className="border border-red-200 bg-red-50 rounded-xl p-4">
        <h2 className="text-red-800 font-semibold mb-1">An error occurred</h2>
        <p className="text-red-700 text-sm">{error}</p>
      </section>
    );
  }

  const current = STATUS_COPY[status];

  return (
    <section className={`border rounded-xl p-4 ${current.tone}`}>
      <h2 className="font-semibold">{current.title}</h2>
      {filename && (
        <p className="text-sm mt-1">
          Current file: <span className="font-medium">{filename}</span>
        </p>
      )}
      {loading && <p className="text-sm mt-1">Please wait...</p>}
    </section>
  );
}
