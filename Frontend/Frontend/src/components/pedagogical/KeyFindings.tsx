// components/pedagogical/KeyFindings.tsx
// ==========================================
// NEW component. Replaces the old "list every conforming session" block
// (AuditPlanningView) — which was both slow to render (grid of every
// single session, grouped by day) and useless (its per-session status
// was hardcoded to "passed" in PedagogicalAuditPage.tsx, so it never
// actually reflected the audit at the session level anyway).
//
// What's actually valuable to an admin: which criteria are doing well
// (so they know what NOT to touch) and which need attention first
// (prioritized, HIGH severity first) — at the criterion level, which is
// the level the backend genuinely audits at.

import type { CriterionResult } from "../../types/pedagogical";

interface KeyFindingsProps {
  strengths: CriterionResult[];   // top passed criteria
  issues:    CriterionResult[];   // top failed criteria, worst first
  onSelect?: (criterion: CriterionResult) => void;
}

const MAX_ITEMS = 3;

function severityLabel(severity: CriterionResult["severity"]): string {
  return { high: "High priority", medium: "Medium priority", low: "Low priority" }[severity];
}

export default function KeyFindings({ strengths, issues, onSelect }: KeyFindingsProps) {
  const topStrengths = strengths.slice(0, MAX_ITEMS);
  const topIssues     = issues.slice(0, MAX_ITEMS);

  if (topStrengths.length === 0 && topIssues.length === 0) return null;

  return (
    <div className="grid gap-5 md:grid-cols-2">

      {/* Strengths */}
      <section className="rounded-3xl border border-emerald-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-2">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-700">
            What is working well
          </p>
        </div>
        {topStrengths.length === 0 ? (
          <p className="mt-4 text-sm text-slate-400">No compliant criteria yet.</p>
        ) : (
          <ul className="mt-4 space-y-3">
            {topStrengths.map((c) => (
              <li key={c.rule}>
                <button
                  type="button"
                  onClick={() => onSelect?.(c)}
                  className="w-full rounded-2xl border border-emerald-100 bg-emerald-50/60 p-3 text-left transition hover:border-emerald-200"
                >
                  <p className="text-sm font-semibold text-slate-800">{c.rule}</p>
                  <p className="mt-0.5 text-xs leading-relaxed text-slate-600 line-clamp-2">
                    {c.message}
                  </p>
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Issues */}
      <section className="rounded-3xl border border-rose-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-2">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-rose-700">
            Needs priority fixes
          </p>
        </div>
        {topIssues.length === 0 ? (
          <p className="mt-4 text-sm text-slate-400">No blocking issues detected 🎉</p>
        ) : (
          <ul className="mt-4 space-y-3">
            {topIssues.map((c) => (
              <li key={c.rule}>
                <button
                  type="button"
                  onClick={() => onSelect?.(c)}
                  className="w-full rounded-2xl border border-rose-100 bg-rose-50/60 p-3 text-left transition hover:border-rose-200"
                >
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-semibold text-slate-800">{c.rule}</p>
                    <span className="shrink-0 rounded-full bg-white px-2 py-0.5 text-[10px] font-semibold text-rose-600 border border-rose-200">
                      {severityLabel(c.severity)}
                    </span>
                  </div>
                  <p className="mt-0.5 text-xs leading-relaxed text-slate-600 line-clamp-2">
                    {c.message}
                  </p>
                  {c.recommendation && (
                    <p className="mt-1.5 text-xs font-medium text-rose-700">
                      {c.recommendation}
                    </p>
                  )}
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}