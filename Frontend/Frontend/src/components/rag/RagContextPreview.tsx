// src/components/rag/RagContextPreview.tsx
// Shows which saved information can help each planning step.

import { useState } from "react";
import {
  Search,
  CalendarDays,
  ClipboardList,
  GraduationCap,
  Loader2,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";
import { useRAG } from "../../hooks/useRAG";

const AGENTS = [
  { key: "planning",    label: "Build a schedule",    Icon: CalendarDays,   desc: "Preferences for your timetable" },
  { key: "constraint",  label: "Check your needs",  Icon: ClipboardList,  desc: "Availability and personal requests" },
  { key: "pedagogical", label: "Improve learning", Icon: GraduationCap,  desc: "Guidance for a better experience" },
] as const;

interface Props { userId: string; }

export default function RagContextPreview({ userId }: Props) {
  const {
    context, isLoading,
    fetchPlanningContext, fetchConstraintContext, fetchPedagogicalContext,
  } = useRAG();
  const [activeAgent, setActiveAgent] = useState<"planning" | "constraint" | "pedagogical" | null>(null);

  const handleFetch = async (agent: typeof AGENTS[number]["key"]) => {
    setActiveAgent(agent);
    if (agent === "planning")    await fetchPlanningContext(userId);
    if (agent === "constraint")  await fetchConstraintContext(userId);
    if (agent === "pedagogical") await fetchPedagogicalContext(userId);
  };

  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      {/* Header */}
      <header className="flex items-start gap-3 border-b border-slate-100 bg-linear-to-br from-slate-50 via-white to-white px-5 py-4">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-900 text-white shadow-sm">
          <Search className="h-4 w-4" aria-hidden="true" />
        </span>
        <div className="min-w-0">
          <h3 className="text-sm font-semibold tracking-tight text-slate-900">
            How your choices help
          </h3>
          <p className="mt-0.5 text-xs text-slate-500">
            Choose a planning step to see what information can be useful there.
          </p>
        </div>
      </header>

      {/* Body */}
      <div className="space-y-4 bg-slate-50/40 p-5">
        {/* Agent selector */}
        <div className="grid gap-2 sm:grid-cols-3">
          {AGENTS.map(a => {
            const Icon = a.Icon;
            const isActive = activeAgent === a.key;
            return (
              <button
                key={a.key}
                onClick={() => handleFetch(a.key)}
                disabled={isLoading}
                className={`group flex items-start gap-2.5 rounded-2xl border p-3 text-left transition disabled:opacity-50 ${
                  isActive
                    ? "border-slate-800 bg-slate-900 text-white shadow-sm"
                    : "border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:shadow-sm"
                }`}
              >
                <span
                  className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${
                    isActive ? "bg-white/10 text-white" : "bg-slate-100 text-slate-500"
                  }`}
                >
                  <Icon className="h-3.5 w-3.5" aria-hidden="true" />
                </span>
                <div className="min-w-0">
                  <p className="truncate text-xs font-semibold">{a.label}</p>
                  <p
                    className={`mt-0.5 line-clamp-2 text-[10px] ${
                      isActive ? "text-white/70" : "text-slate-500"
                    }`}
                  >
                    {a.desc}
                  </p>
                </div>
              </button>
            );
          })}
        </div>

        {/* Loading */}
        {isLoading && (
          <div className="flex items-center justify-center gap-2 rounded-2xl border border-slate-100 bg-white py-8 text-xs text-slate-500">
            <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
            Looking at your saved preferences…
          </div>
        )}

        {/* Context */}
        {!isLoading && context && (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              {context.has_context ? (
                <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-100 bg-emerald-50 px-3 py-1 text-[11px] font-semibold text-emerald-700">
                  <CheckCircle2 className="h-3 w-3" aria-hidden="true" />
                  {context.memory_count} helpful detail{context.memory_count === 1 ? "" : "s"} found
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-[11px] font-semibold text-slate-500">
                  Nothing saved for this step yet
                </span>
              )}
            </div>

            {context.has_context ? (
              <div className="rounded-2xl border border-emerald-100 bg-emerald-50/60 p-4 text-xs leading-relaxed text-emerald-800">
                Your saved choices and feedback can help make this part of the planning process more relevant to you.
              </div>
            ) : (
              <div className="flex items-start gap-2.5 rounded-2xl border border-amber-100 bg-amber-50/60 p-4">
                <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-600" aria-hidden="true" />
                <p className="text-xs leading-relaxed text-amber-800">
                  There is not enough saved information for this step yet. Review a schedule or add a preference to get started.
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}