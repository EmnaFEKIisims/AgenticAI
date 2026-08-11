interface RecommendationListProps {
  recommendations: string[];
}

export default function RecommendationList({ recommendations }: RecommendationListProps) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
        Recommendations
      </p>
      <h3 className="mt-1 text-lg font-bold text-slate-900">Actions proposees</h3>

      {recommendations.length === 0 ? (
        <div className="mt-5 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-5 text-sm text-slate-500">
          Aucune recommandation retournee par le backend.
        </div>
      ) : (
        <ol className="mt-5 space-y-3">
          {recommendations.map((recommendation, index) => (
            <li
              key={`${recommendation}-${index}`}
              className="rounded-2xl border border-slate-200 bg-linear-to-r from-slate-50 to-white p-4"
            >
              <div className="flex items-start gap-3">
                <span className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-900 text-xs font-bold text-white">
                  {index + 1}
                </span>
                <p className="pt-0.5 text-sm leading-relaxed text-slate-700">{recommendation}</p>
              </div>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
