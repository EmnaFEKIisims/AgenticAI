// components/pedagogical/NarrativeSummary.tsx
// ================================================
// NEW component. The pedagogical agent's backend already produces a
// human-readable paragraph (LLM-generated in node_explain, see
// agents/pedagogical_agent.py) — it states the compliance level, names
// 2-3 strengths, 2-3 weaknesses, and gives one concrete recommendation.
// This IS the single most valuable piece of the whole report: it's
// already written for a human administrator to read and act on.
//
// It was previously buried as recommendations[0] inside a generic
// numbered list (RecommendationList), indistinguishable from the raw
// scoring-service action items. This component gives it the prominence
// it deserves — a real "executive summary" a busy admin can read in 10
// seconds and understand what to do next.

interface NarrativeSummaryProps {
  narrative:   string;
  isCompliant: boolean;
}

export default function NarrativeSummary({ narrative, isCompliant }: NarrativeSummaryProps) {
  if (!narrative) return null;

  return (
    <div className={`rounded-3xl border p-6 ${
      isCompliant
        ? "border-emerald-200 bg-emerald-50/50"
        : "border-amber-200 bg-amber-50/50"
    }`}>
      <div className="flex items-start gap-3">
        <span className="text-2xl leading-none">{isCompliant ? "✅" : "🔎"}</span>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
            Summary
          </p>
          <p className="mt-2 text-sm leading-relaxed text-slate-700">
            {narrative}
          </p>
        </div>
      </div>
    </div>
  );
}