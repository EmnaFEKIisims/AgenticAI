import { Loader2 } from "lucide-react";

interface LoadingOverlayProps {
  visible: boolean;
  step?: string;
}

export default function LoadingOverlay({ visible, step = "Analyzing constraints..." }: LoadingOverlayProps) {
  if (!visible) {
    return null;
  }

  const stages = ["ConstraintAgent", "Analyzer", "Validator", "Merger"];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 px-4 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-3xl border border-white/20 bg-white p-6 shadow-2xl shadow-slate-900/30">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-900 text-white">
            <Loader2 className="h-6 w-6 animate-spin" aria-hidden="true" />
          </div>
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
              Processing
            </p>
            <h3 className="text-lg font-bold text-slate-900">{step}</h3>
          </div>
        </div>

        <div className="mt-6 space-y-3">
          {stages.map((stage, index) => (
            <div key={stage} className="flex items-center gap-3">
              <span
                className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-semibold ${
                  index === 0 ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-500"
                }`}
              >
                {index + 1}
              </span>
              <span className="text-sm text-slate-700">{stage}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
