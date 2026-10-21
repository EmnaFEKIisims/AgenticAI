import { Lightbulb, ArrowRight } from "lucide-react";

interface RecommendationListProps {
  recommendations: string[];
}

export default function RecommendationList({ recommendations }: RecommendationListProps) {
  return (
    <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      {/* Header */}
      <header className="flex items-start gap-4 border-b border-slate-100 bg-linear-to-br from-slate-50 via-white to-white px-6 py-5 sm:px-8">
        <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-amber-200 bg-amber-100 text-amber-700 shadow-sm">
          <Lightbulb className="h-5 w-5" aria-hidden="true" />
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="text-base font-semibold tracking-tight text-slate-900">
            Proposed actions
          </h3>
          <p className="mt-0.5 text-sm text-slate-500">
            Prioritized recommendations from the audit.
          </p>
        </div>
        <span className="shrink-0 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-600">
          {recommendations.length}
        </span>
      </header>

      <div className="bg-slate-50/40 p-6 sm:p-8">
        {recommendations.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-slate-200 bg-white py-12 text-center">
            <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-50 text-slate-400">
              <Lightbulb className="h-5 w-5" aria-hidden="true" />
            </span>
            <p className="text-sm text-slate-500">
              Aucune recommandation retournée par le backend.
            </p>
          </div>
        ) : (
          <ol className="space-y-2.5">
            {recommendations.map((recommendation, index) => (
              <li
                key={`${recommendation}-${index}`}
                className="group rounded-2xl border border-slate-100 bg-white p-4 shadow-sm transition hover:border-slate-200 hover:shadow"
              >
                <div className="flex items-start gap-3">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border border-amber-200 bg-amber-100 font-mono text-xs font-bold text-amber-700">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <p className="pt-0.5 text-sm leading-relaxed text-slate-700">
                    {recommendation}
                  </p>
                  <ArrowRight className="mt-0.5 ml-auto h-4 w-4 shrink-0 text-slate-300 transition group-hover:text-slate-500" aria-hidden="true" />
                </div>
              </li>
            ))}
          </ol>
        )}
      </div>
    </section>
  );
}