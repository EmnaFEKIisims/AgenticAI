// src/components/rag/RagStatus.tsx
// Shows Qdrant connection status + memory count.

import { useEffect, useState } from "react";
import {
  Database,
  Brain,
  Boxes,
  CheckCircle2,
  XCircle,
  Loader2,
} from "lucide-react";

interface Props { userId: string; total: number; }

export default function RagStatus({ userId, total }: Props) {
  const [qdrantOk, setQdrantOk] = useState<boolean | null>(null);

  useEffect(() => {
    fetch("http://localhost:6333/collections")
      .then(r => setQdrantOk(r.ok))
      .catch(() => setQdrantOk(false));
  }, []);

  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      {/* Header */}
      <header className="flex items-center gap-3 border-b border-slate-100 bg-slate-50 px-5 py-4">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-900 text-white shadow-sm">
          <Boxes className="h-4 w-4" aria-hidden="true" />
        </span>
        <div>
          <h3 className="text-sm font-semibold tracking-tight text-slate-900">
            RAG system status
          </h3>
          <p className="text-xs text-slate-500">
            Vector store and embedding information.
          </p>
        </div>
      </header>

      {/* Body */}
      <div className="space-y-2 bg-slate-50/40 p-5">
        {/* Qdrant */}
        <div className="flex items-center justify-between gap-3 rounded-2xl border border-slate-100 bg-white px-4 py-3 shadow-sm">
          <div className="flex items-center gap-3">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-500">
              <Database className="h-3.5 w-3.5" aria-hidden="true" />
            </span>
            <div>
              <p className="text-xs font-semibold text-slate-800">Qdrant vector DB</p>
              <p className="font-mono text-[10px] text-slate-400">localhost:6333</p>
            </div>
          </div>

          <span
            className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[10px] font-semibold ${
              qdrantOk === null
                ? "border-slate-200 bg-slate-50 text-slate-500"
                : qdrantOk
                ? "border-emerald-100 bg-emerald-50 text-emerald-700"
                : "border-rose-100 bg-rose-50 text-rose-700"
            }`}
          >
            {qdrantOk === null ? (
              <>
                <Loader2 className="h-2.5 w-2.5 animate-spin" aria-hidden="true" />
                Checking
              </>
            ) : qdrantOk ? (
              <>
                <CheckCircle2 className="h-2.5 w-2.5" aria-hidden="true" />
                Connected
              </>
            ) : (
              <>
                <XCircle className="h-2.5 w-2.5" aria-hidden="true" />
                Offline
              </>
            )}
          </span>
        </div>

        {/* Memories */}
        <div className="flex items-center justify-between gap-3 rounded-2xl border border-slate-100 bg-white px-4 py-3 shadow-sm">
          <div className="flex items-center gap-3">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">
              <Brain className="h-3.5 w-3.5" aria-hidden="true" />
            </span>
            <div>
              <p className="text-xs font-semibold text-slate-800">Stored vectors</p>
              <p className="font-mono text-[10px] text-slate-400">
                user {userId.slice(0, 8)}
              </p>
            </div>
          </div>

          <span className="font-mono text-lg font-bold text-slate-900">{total}</span>
        </div>

        {/* Embedding model */}
        <div className="flex items-center justify-between gap-3 rounded-2xl border border-slate-100 bg-white px-4 py-3 shadow-sm">
          <div className="flex items-center gap-3">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-sky-50 text-sky-600">
              <Boxes className="h-3.5 w-3.5" aria-hidden="true" />
            </span>
            <div>
              <p className="text-xs font-semibold text-slate-800">Embedding model</p>
              <p className="font-mono text-[10px] text-slate-400">
                all-MiniLM-L6-v2 · 384 dims
              </p>
            </div>
          </div>

          <span className="inline-flex items-center rounded-full border border-sky-100 bg-sky-50 px-2.5 py-0.5 text-[10px] font-semibold text-sky-700">
            Local
          </span>
        </div>
      </div>
    </div>
  );
}