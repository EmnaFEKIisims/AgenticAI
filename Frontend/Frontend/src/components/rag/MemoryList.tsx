// src/components/rag/MemoryList.tsx

import type { MemoryType } from "../../types/rag";
import { useMemory }       from "../../hooks/useMemory";
import MemoryCard          from "./MemoryCard";

const FILTERS: { value: MemoryType | "all"; label: string; icon: string }[] = [
  { value: "all",                   label: "All",         icon: "🧠" },
  { value: "user_feedback",         label: "Feedback",    icon: "💬" },
  { value: "user_preference",       label: "Preferences", icon: "⚙️"  },
  { value: "decision_history",      label: "Decisions",   icon: "📋" },
  { value: "conflict_correction",   label: "Conflicts",   icon: "⚠️" },
  { value: "planning_history",      label: "Plannings",   icon: "📅" },
  { value: "pedagogical_knowledge", label: "Rules",       icon: "🎓" },
];

interface Props { userId: string; }

export default function MemoryList({ userId }: Props) {
  const {
    memories, summary, filterType, isLoading, error,
    setFilterType, refresh, onDelete, onClearAll,
  } = useMemory(userId);

  return (
    <div className="rounded-3xl border border-slate-200 bg-white shadow-sm overflow-hidden">

      {/* Header */}
      <div className="border-b border-slate-100 px-5 py-4 flex items-center justify-between">
        <div>
          <p className="text-sm font-bold text-slate-900">🧠 Memory Vectors</p>
          <p className="text-xs text-slate-400">{summary.total} stored in Qdrant</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => void refresh()}
            className="rounded-xl border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50">
            ↺
          </button>
          {summary.total > 0 && (
            <button onClick={() => { if (confirm("Clear all memories?")) void onClearAll(); }}
              className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-1.5 text-xs font-semibold text-rose-700 hover:bg-rose-100">
              🗑 Clear
            </button>
          )}
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1 px-4 py-2 border-b border-slate-100 overflow-x-auto">
        {FILTERS.map(f => (
          <button key={f.value} onClick={() => setFilterType(f.value)}
            className={`shrink-0 rounded-lg px-3 py-1 text-xs font-medium flex items-center gap-1 transition ${
              filterType === f.value ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"
            }`}>
            {f.icon} {f.label}
            <span className={`text-[10px] ${filterType === f.value ? "text-slate-300" : "text-slate-400"}`}>
              {f.value === "all" ? summary.total : (summary.by_type[f.value as MemoryType] ?? 0)}
            </span>
          </button>
        ))}
      </div>

      {/* Error */}
      {error && (
        <div className="mx-4 mt-3 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
          ❌ {error}
        </div>
      )}

      {/* List */}
      <div className="max-h-96 overflow-y-auto p-4 space-y-2">
        {isLoading && <p className="text-center text-xs text-slate-400 py-6">Loading from Qdrant…</p>}
        {!isLoading && memories.length === 0 && (
          <div className="text-center py-8">
            <p className="text-3xl mb-2">🧠</p>
            <p className="text-xs font-semibold text-slate-600">No memories yet</p>
            <p className="text-xs text-slate-400 mt-1">
              Memories are created when you generate, validate, or give feedback on plannings.
            </p>
          </div>
        )}
        {memories.map(m => (
          <MemoryCard key={m.id} memory={m} onDelete={onDelete} />
        ))}
      </div>
    </div>
  );
}