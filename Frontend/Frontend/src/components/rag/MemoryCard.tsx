// src/components/rag/MemoryCard.tsx

import {
  AlertTriangle,
  CalendarDays,
  ClipboardList,
  GraduationCap,
  MessageSquareText,
  Settings2,
  Star,
  X,
  type LucideIcon,
} from "lucide-react";
import type { Memory } from "../../types/memory";
import type { MemoryType } from "../../types/rag";

const TYPE_CONFIG: Record<MemoryType, { icon: LucideIcon; color: string; label: string }> = {
  user_preference:       { icon: Settings2,      color: "text-sky-700    bg-sky-50    border-sky-200",    label: "Preference"  },
  decision_history:      { icon: ClipboardList,  color: "text-violet-700 bg-violet-50 border-violet-200", label: "Decision"    },
  planning_history:      { icon: CalendarDays,   color: "text-indigo-700 bg-indigo-50 border-indigo-200", label: "Planning"    },
  conflict_correction:   { icon: AlertTriangle,  color: "text-amber-700  bg-amber-50  border-amber-200",  label: "Conflict"    },
  user_feedback:         { icon: MessageSquareText, color: "text-emerald-700 bg-emerald-50 border-emerald-200", label: "Feedback" },
  pedagogical_knowledge: { icon: GraduationCap,  color: "text-rose-700   bg-rose-50   border-rose-200",   label: "Rule"        },
};

interface Props {
  memory:   Memory;
  onDelete: (id: string) => void;
}

export default function MemoryCard({ memory, onDelete }: Props) {
  const cfg = TYPE_CONFIG[memory.type] ?? TYPE_CONFIG.user_preference;
  const Icon = cfg.icon;

  return (
    <div className={`group rounded-2xl border p-3 transition hover:shadow-sm ${cfg.color.split(" ").slice(1).join(" ")}`}>
      <div className="flex gap-2">
        <Icon className={`mt-0.5 h-3.5 w-3.5 shrink-0 ${cfg.color.split(" ")[0]}`} aria-hidden="true" />
        <div className="min-w-0 flex-1">
          <div className="mb-1 flex items-center gap-2">
            <span className={`text-[10px] font-bold uppercase tracking-wider ${cfg.color.split(" ")[0]}`}>
              {cfg.label}
            </span>
          </div>
          <p className="line-clamp-3 text-xs text-slate-700">{memory.content}</p>
          {memory.created_at && (
            <p className="mt-1.5 text-[10px] text-slate-400">
              {new Date(memory.created_at).toLocaleString("en-GB", {
                day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
              })}
            </p>
          )}
        </div>
        <button onClick={() => onDelete(memory.id)}
          className="shrink-0 text-xs font-bold text-slate-300 opacity-0 transition hover:text-rose-500 group-hover:opacity-100"
          aria-label="Delete memory"
        >
          <X className="h-3.5 w-3.5" aria-hidden="true" />
        </button>
      </div>
    </div>
  );
}