// src/components/rag/RagStatus.tsx
// Shows Qdrant connection status + memory count.

import { useEffect, useState } from "react";

interface Props { userId: string; total: number; }

export default function RagStatus({ userId, total }: Props) {
  const [qdrantOk, setQdrantOk] = useState<boolean | null>(null);

  useEffect(() => {
    fetch("http://localhost:6333/collections")
      .then(r => setQdrantOk(r.ok))
      .catch(() => setQdrantOk(false));
  }, []);

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm space-y-3">
      <p className="text-xs font-bold uppercase tracking-wider text-slate-500">RAG System Status</p>

      <div className="space-y-2">
        {/* Qdrant */}
        <div className="flex items-center justify-between rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3">
          <div className="flex items-center gap-2">
            <span className="text-base">⚡</span>
            <div>
              <p className="text-xs font-semibold text-slate-700">Qdrant Vector DB</p>
              <p className="text-[10px] text-slate-400">localhost:6333</p>
            </div>
          </div>
          <span className={`rounded-lg px-2 py-0.5 text-[10px] font-bold ${
            qdrantOk === null  ? "bg-slate-100 text-slate-500" :
            qdrantOk           ? "bg-emerald-100 text-emerald-700" :
                                 "bg-rose-100 text-rose-700"
          }`}>
            {qdrantOk === null ? "Checking…" : qdrantOk ? "Connected ✅" : "Offline ❌"}
          </span>
        </div>

        {/* Memories */}
        <div className="flex items-center justify-between rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3">
          <div className="flex items-center gap-2">
            <span className="text-base">🧠</span>
            <div>
              <p className="text-xs font-semibold text-slate-700">Stored Vectors</p>
              <p className="text-[10px] text-slate-400">user {userId.slice(0, 8)}...</p>
            </div>
          </div>
          <span className="text-xl font-bold text-slate-900">{total}</span>
        </div>

        {/* Embedding model */}
        <div className="flex items-center justify-between rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3">
          <div className="flex items-center gap-2">
            <span className="text-base">🔢</span>
            <div>
              <p className="text-xs font-semibold text-slate-700">Embedding Model</p>
              <p className="text-[10px] text-slate-400">all-MiniLM-L6-v2 · 384 dims</p>
            </div>
          </div>
          <span className="rounded-lg bg-sky-100 px-2 py-0.5 text-[10px] font-bold text-sky-700">Local</span>
        </div>
      </div>
    </div>
  );
}