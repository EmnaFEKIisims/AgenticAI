import {
  Clock,
  UploadCloud,
  Loader2,
  Eye,
  CheckCircle2,
  XCircle,
  AlertTriangle,
} from 'lucide-react';

interface DataStatusProps {
  status: 'idle' | 'uploading' | 'processing' | 'preview' | 'validated' | 'rejected';
  loading: boolean;
  error: string | null;
  filename: string;
}

const STATUS_COPY: Record<
  DataStatusProps['status'],
  { title: string; tone: string; iconBg: string; Icon: React.ElementType; spinning?: boolean }
> = {
  idle: {
    title: 'Waiting for file upload',
    tone: 'border-slate-200 bg-slate-50/60 text-slate-700',
    iconBg: 'bg-slate-100 text-slate-600',
    Icon: Clock,
  },
  uploading: {
    title: 'Uploading file…',
    tone: 'border-sky-100 bg-sky-50/60 text-sky-800',
    iconBg: 'bg-sky-100 text-sky-600',
    Icon: UploadCloud,
    spinning: true,
  },
  processing: {
    title: 'Processing records…',
    tone: 'border-amber-100 bg-amber-50/60 text-amber-800',
    iconBg: 'bg-amber-100 text-amber-600',
    Icon: Loader2,
    spinning: true,
  },
  preview: {
    title: 'Preview ready for review',
    tone: 'border-sky-100 bg-sky-50/60 text-sky-800',
    iconBg: 'bg-sky-100 text-sky-600',
    Icon: Eye,
  },
  validated: {
    title: 'Data validated and accepted',
    tone: 'border-emerald-100 bg-emerald-50/60 text-emerald-800',
    iconBg: 'bg-emerald-100 text-emerald-600',
    Icon: CheckCircle2,
  },
  rejected: {
    title: 'Upload rejected',
    tone: 'border-rose-100 bg-rose-50/60 text-rose-800',
    iconBg: 'bg-rose-100 text-rose-600',
    Icon: XCircle,
  },
};

export default function DataStatus({ status, loading, error, filename }: DataStatusProps) {
  if (error) {
    return (
      <section className="overflow-hidden rounded-2xl border border-rose-100 bg-rose-50/60 shadow-sm">
        <div className="flex items-start gap-3 p-4 sm:p-5">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white text-rose-600 shadow-sm">
            <AlertTriangle className="h-4 w-4" aria-hidden="true" />
          </span>
          <div className="min-w-0">
            <h2 className="text-sm font-semibold text-rose-900">An error occurred</h2>
            <p className="mt-0.5 text-sm text-rose-800/80">{error}</p>
          </div>
        </div>
      </section>
    );
  }

  const current = STATUS_COPY[status];
  const Icon = current.Icon;

  return (
    <section className={`overflow-hidden rounded-2xl border shadow-sm ${current.tone}`}>
      <div className="flex items-start gap-3 p-4 sm:p-5">
        <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${current.iconBg}`}>
          <Icon
            className={`h-4 w-4 ${current.spinning ? 'animate-spin' : ''}`}
            aria-hidden="true"
          />
        </span>
        <div className="min-w-0 flex-1">
          <h2 className="text-sm font-semibold">{current.title}</h2>
          {filename && (
            <p className="mt-0.5 text-xs opacity-80">
              File: <span className="font-medium">{filename}</span>
            </p>
          )}
          {loading && (
            <p className="mt-0.5 text-xs opacity-70">
              Please wait, this can take a few seconds…
            </p>
          )}
        </div>
      </div>
    </section>
  );
}