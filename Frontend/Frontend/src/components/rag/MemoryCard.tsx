// src/components/rag/MemoryCard.tsx

import type { Memory }    from "../../types/memory";
import type { MemoryType } from "../../types/rag";

const TYPE_CONFIG: Record<MemoryType, { icon: string; color: string; label: string }> = {
  user_preference:       { icon: "⚙️",  color: "text-sky-700    bg-sky-50    border-sky-200",    label: "Preference"  },
  decision_history:      { icon: "📋", color: "text-violet-700 bg-violet-50 border-violet-200", label: "Decision"    },
  planning_history:      { icon: "📅", color: "text-indigo-700 bg-indigo-50 border-indigo-200", label: "Planning"    },
  conflict_correction:   { icon: "⚠️", color: "text-amber-700  bg-amber-50  border-amber-200",  label: "Conflict"    },
  user_feedback:         { icon: "💬", color: "text-emerald-700 bg-emerald-50 border-emerald-200", label: "Feedback" },
  pedagogical_knowledge: { icon: "🎓", color: "text-rose-700   bg-rose-50   border-rose-200",   label: "Rule"        },
};

interface Props {
  memory:   Memory;
  onDelete: (id: string) => void;
}

export default function MemoryCard({ memory, onDelete }: Props) {
  const cfg = TYPE_CONFIG[memory.type] ?? TYPE_CONFIG.user_preference;

  return (
    <div className={`group rounded-2xl border p-3 transition hover:shadow-sm ${cfg.color.split(" ").slice(1).join(" ")}`}>
      <div className="flex gap-2">
        <span className="text-sm shrink-0 mt-0.5">{cfg.icon}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-[10px] font-bold uppercase tracking-wider ${cfg.color.split(" ")[0]}`}>
              {cfg.label}
            </span>
            {Array.from({ length: memory.importance }).map((_, i) => (
              <span key={i} className="text-[10px] text-amber-500">★</span>
            ))}
          </div>
          <p className="text-xs text-slate-700 line-clamp-3">{memory.content}</p>
          {memory.created_at && (
            <p className="text-[10px] text-slate-400 mt-1.5">
              {new Date(memory.created_at).toLocaleString("en-GB", {
                day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
              })}
            </p>
          )}
        </div>
        <button onClick={() => onDelete(memory.id)}
          className="opacity-0 group-hover:opacity-100 shrink-0 text-slate-300 hover:text-rose-500 text-xs font-bold transition">
          ✕
        </button>
      </div>
    </div>
  );
}