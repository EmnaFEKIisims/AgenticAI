// src/components/rag/MemoryList.tsx

import {
  Brain,
  MessageSquare,
  Settings,
  ClipboardList,
  AlertTriangle,
  CalendarDays,
  GraduationCap,
  RefreshCw,
  Trash2,
  Loader2,
} from "lucide-react";
import type { MemoryType } from "../../types/rag";
import { useMemory } from "../../hooks/useMemory";
import MemoryCard from "./MemoryCard";

const FILTERS: {
  value: MemoryType | "all";
  label: string;
  Icon: React.ElementType;
}[] = [
  { value: "all",                   label: "All",         Icon: Brain },
  { value: "user_feedback",         label: "Feedback",    Icon: MessageSquare },
  { value: "user_preference",       label: "Preferences", Icon: Settings },
  { value: "decision_history",      label: "Decisions",   Icon: ClipboardList },
  { value: "conflict_correction",   label: "Conflicts",   Icon: AlertTriangle },
  { value: "planning_history",      label: "Plannings",   Icon: CalendarDays },
  { value: "pedagogical_knowledge", label: "Rules",       Icon: GraduationCap },
];

interface Props { userId: string; }

export default function MemoryList({ userId }: Props) {
  const {
    memories, summary, filterType, isLoading, error,
    setFilterType, refresh, onDelete, onClearAll,
  } = useMemory(userId);

  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      {/* Header */}
      <header className="flex items-center justify-between gap-3 border-b border-slate-100 bg-slate-50 px-5 py-4">
        <div className="flex items-center gap-3">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-900 text-white shadow-sm">
            <Brain className="h-4 w-4" aria-hidden="true" />
          </span>
          <div>
            <h3 className="text-sm font-semibold tracking-tight text-slate-900">
              Memory vectors
            </h3>
            <p className="text-xs text-slate-500">
              {summary.total} stored in Qdrant
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          <button
            onClick={() => void refresh()}
            disabled={isLoading}
            className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 transition hover:border-slate-300 hover:bg-slate-50 disabled:opacity-50"
            title="Refresh"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} aria-hidden="true" />
          </button>

          {summary.total > 0 && (
            <button
              onClick={() => { if (confirm("Clear all memories?")) void onClearAll(); }}
              className="inline-flex items-center gap-1.5 rounded-lg border border-rose-100 bg-rose-50/60 px-2.5 py-1.5 text-[11px] font-semibold text-rose-700 transition hover:border-rose-200 hover:bg-rose-50"
            >
              <Trash2 className="h-3 w-3" aria-hidden="true" />
              Clear
            </button>
          )}
        </div>
      </header>

      {/* Filters */}
      <div className="flex gap-1 overflow-x-auto border-b border-slate-100 px-4 py-2.5">
        {FILTERS.map(f => {
          const Icon = f.Icon;
          const isActive = filterType === f.value;
          const count = f.value === "all"
            ? summary.total
            : (summary.by_type[f.value as MemoryType] ?? 0);

          return (
            <button
              key={f.value}
              onClick={() => setFilterType(f.value)}
              className={`inline-flex shrink-0 items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium transition ${
                isActive
                  ? "bg-slate-900 text-white shadow-sm"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              <Icon className="h-3 w-3" aria-hidden="true" />
              {f.label}
              <span
                className={`font-mono text-[10px] ${
                  isActive ? "text-slate-300" : "text-slate-400"
                }`}
              >
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Error */}
      {error && (
        <div className="mx-4 mt-3 flex items-start gap-2 rounded-xl border border-rose-100 bg-rose-50/70 p-3">
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-rose-600" aria-hidden="true" />
          <p className="text-xs text-rose-800">{error}</p>
        </div>
      )}

      {/* List */}
      <div className="max-h-96 space-y-2 overflow-y-auto bg-slate-50/40 p-4">
        {isLoading && (
          <div className="flex items-center justify-center gap-2 py-8 text-xs text-slate-500">
            <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
            Loading from Qdrant…
          </div>
        )}

        {!isLoading && memories.length === 0 && (
          <div className="flex flex-col items-center gap-3 py-10 text-center">
            <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-slate-400 shadow-sm">
              <Brain className="h-5 w-5" aria-hidden="true" />
            </span>
            <div className="space-y-1">
              <p className="text-sm font-semibold text-slate-700">No memories yet</p>
              <p className="max-w-xs text-xs text-slate-400">
                Memories are created when you generate, validate, or give feedback on plannings.
              </p>
            </div>
          </div>
        )}

        {memories.map(m => (
          <MemoryCard key={m.id} memory={m} onDelete={onDelete} />
        ))}
      </div>
    </div>
  );
}