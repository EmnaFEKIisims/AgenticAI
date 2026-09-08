// src/components/rag/DocumentItem.tsx

import type { KnowledgeDocument } from "../../types/rag";

interface Props { doc: KnowledgeDocument; }

export default function DocumentItem({ doc }: Props) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3">
      <span className="text-xl shrink-0">📄</span>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-slate-800 truncate">{doc.title}</p>
        <p className="text-xs text-slate-400">{doc.source ?? "—"} · {doc.chunks} chunk(s)</p>
      </div>
      <span className={`shrink-0 rounded-lg px-2 py-0.5 text-[10px] font-bold ${
        doc.is_indexed ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"
      }`}>
        {doc.is_indexed ? "Indexed ✅" : "Pending"}
      </span>
    </div>
  );
}