import { Loader2 } from "lucide-react";

interface LoadingOverlayProps {
  visible: boolean;
  step?: string;
}

export default function LoadingOverlay({ visible, step = "Analyzing constraints..." }: LoadingOverlayProps) {
  if (!visible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 px-4 backdrop-blur-md">
      <div className="relative w-full max-w-sm overflow-hidden rounded-3xl border border-white/20 bg-white p-8 text-center shadow-2xl">
        <div className="pointer-events-none absolute inset-x-0 -top-24 h-48 bg-linear-to-b from-slate-100/80 to-transparent" />

        <div className="relative mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-900 text-white shadow-lg">
          <Loader2 className="h-7 w-7 animate-spin" aria-hidden="true" />
        </div>

        <h3 className="relative mt-6 text-base font-semibold text-slate-900">{step}</h3>
        <p className="relative mt-1 text-sm text-slate-500">
          Please wait, this may take a few seconds.
        </p>

        <div className="relative mt-6 flex justify-center gap-1.5">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="h-1.5 w-1.5 animate-pulse rounded-full bg-slate-300"
              style={{ animationDelay: `${i * 150}ms` }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}