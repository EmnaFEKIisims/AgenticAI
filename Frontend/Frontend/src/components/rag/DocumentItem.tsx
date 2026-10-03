// src/components/rag/DocumentItem.tsx

import { FileText, CheckCircle2, Clock } from "lucide-react";
import type { KnowledgeDocument } from "../../types/rag";

interface Props { doc: KnowledgeDocument; }

export default function DocumentItem({ doc }: Props) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-slate-100 bg-white px-4 py-3 shadow-sm transition hover:border-slate-200 hover:shadow">
      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-slate-100 bg-slate-50 text-slate-500">
        <FileText className="h-4 w-4" aria-hidden="true" />
      </span>

      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-semibold text-slate-800">{doc.title}</p>
        <p className="mt-0.5 truncate text-xs text-slate-400">
          {doc.source ?? "—"}
          <span className="mx-1.5 text-slate-300">·</span>
          {doc.is_indexed ? "Ready to use" : "Being prepared"}
        </p>
      </div>

      <span
        className={`inline-flex shrink-0 items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-semibold ${
          doc.is_indexed
            ? "border-emerald-100 bg-emerald-50 text-emerald-700"
            : "border-amber-100 bg-amber-50 text-amber-700"
        }`}
      >
        {doc.is_indexed ? (
          <>
            <CheckCircle2 className="h-3 w-3" aria-hidden="true" />
            Ready
          </>
        ) : (
          <>
            <Clock className="h-3 w-3" aria-hidden="true" />
            Preparing
          </>
        )}
      </span>
    </div>
  );
}