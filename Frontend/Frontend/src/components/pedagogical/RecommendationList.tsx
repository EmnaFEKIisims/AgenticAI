// components/pedagogical/RecommendationList.tsx
// ← CHANGED: this now receives ONLY the concrete, actionable
//   recommendations (report.recommendations.slice(1) — the backend
//   prepends the LLM narrative paragraph at index 0, see
//   agents/pedagogical_agent.py node_build_report). That narrative now
//   has its own dedicated, more prominent spot (NarrativeSummary.tsx),
//   so this list is no longer a mix of "read this paragraph" + "do this
//   thing" — it's a clean, short action list.

interface RecommendationListProps {
  recommendations: string[];
}

export default function RecommendationList({ recommendations }: RecommendationListProps) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
        Action plan
      </p>
      <h3 className="mt-1 text-lg font-bold text-slate-900">Recommended next steps</h3>

      {recommendations.length === 0 ? (
        <div className="mt-5 rounded-2xl border border-dashed border-emerald-300 bg-emerald-50 p-5 text-sm text-emerald-700">
          🎉 No action required — the plan complies with the audited criteria.
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