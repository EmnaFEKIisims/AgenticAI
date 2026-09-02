// src/components/rag/RagContextPreview.tsx
// Shows what RAG context would be injected into the LLM for a given agent.

import { useState }  from "react";
import { useRAG }    from "../../hooks/useRAG";

const AGENTS = [
  { key: "planning",    label: "🗓️  PlanningAgent",    desc: "Context for schedule generation" },
  { key: "constraint",  label: "📋 ConstraintAgent",   desc: "Context for constraint analysis" },
  { key: "pedagogical", label: "🎓 PedagogicalAgent",  desc: "Context for pedagogical audit"   },
] as const;

interface Props { userId: string; }

export default function RagContextPreview({ userId }: Props) {
  const { context, isLoading, fetchPlanningContext, fetchConstraintContext, fetchPedagogicalContext } = useRAG();
  const [activeAgent, setActiveAgent] = useState<"planning" | "constraint" | "pedagogical" | null>(null);

  const handleFetch = async (agent: typeof AGENTS[number]["key"]) => {
    setActiveAgent(agent);
    if (agent === "planning")    await fetchPlanningContext(userId);
    if (agent === "constraint")  await fetchConstraintContext(userId);
    if (agent === "pedagogical") await fetchPedagogicalContext(userId);
  };

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
      <div>
        <p className="text-xs font-bold uppercase tracking-wider text-slate-500">🔍 RAG Context Preview</p>
        <p className="text-xs text-slate-400 mt-1">
          See what memories will be injected into the LLM before each agent runs.
        </p>
      </div>

      {/* Agent selector */}
      <div className="flex flex-wrap gap-2">
        {AGENTS.map(a => (
          <button key={a.key} onClick={() => handleFetch(a.key)} disabled={isLoading}
            className={`rounded-xl border px-3 py-2 text-xs font-medium transition disabled:opacity-50 ${
              activeAgent === a.key
                ? "border-slate-700 bg-slate-900 text-white"
                : "border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100"
            }`}>
            {a.label}
          </button>
        ))}
      </div>

      {/* Context display */}
      {isLoading && (
        <div className="rounded-2xl border border-slate-100 bg-slate-50 p-4 text-center text-xs text-slate-400">
          Querying Qdrant…
        </div>
      )}

      {!isLoading && context && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className={`rounded-lg px-2 py-0.5 text-[10px] font-bold ${
              context.has_context ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-500"
            }`}>
              {context.has_context ? `✅ ${context.memory_count} memories retrieved` : "No context found"}
            </span>
          </div>

          {context.has_context ? (
            <pre className="rounded-2xl border border-slate-100 bg-slate-50 p-4 text-[10px] text-slate-700 whitespace-pre-wrap overflow-auto max-h-64 font-mono">
              {context.context}
            </pre>
          ) : (
            <div className="rounded-2xl border border-amber-100 bg-amber-50 p-4 text-xs text-amber-700">
              No relevant memories found. Generate and validate some plannings first to build up memory.
            </div>
          )}
        </div>
      )}
    </div>
  );
}