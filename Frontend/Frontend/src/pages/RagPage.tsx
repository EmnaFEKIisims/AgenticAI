// src/pages/rag/RagPage.tsx

import { useState }          from "react";
import { useUser }           from "../hooks/useUser";
import { useMemory }         from "../hooks/useMemory";
import { useRAG }            from "../hooks/useRAG";
import RagStatus             from "../components/rag/RagStatus";
import MemoryList            from "../components/rag/MemoryList";
import RagContextPreview     from "../components/rag/RagContextPreview";
import DocumentUploader      from "../components/rag/DocumentUploader";
import DocumentList          from "../components/rag/DocumentList";

type Tab = "memories" | "context" | "documents";

export default function RagPage() {
  const { userId }                          = useUser();
  const { summary }                         = useMemory(userId);
  const { isLoading: ragLoading, onIngestDocument, onSeedRules } = useRAG();
  const [tab,       setTab]       = useState<Tab>("memories");
  const [seeding,   setSeeding]   = useState(false);
  const [seedDone,  setSeedDone]  = useState(false);

  const handleSeedRules = async () => {
    setSeeding(true);
    await onSeedRules(userId);
    setSeedDone(true);
    setSeeding(false);
    setTimeout(() => setSeedDone(false), 3000);
  };

  return (
    <div className="min-h-screen bg-slate-50">

      {/* Header */}
      <div className="border-b border-slate-200 bg-white px-6 py-5">
        <div className="mx-auto max-w-5xl flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-3xl">🧠</span>
            <div>
              <h1 className="text-xl font-bold text-slate-900">RAG Memory — Qdrant</h1>
              <p className="text-xs text-slate-500 mt-0.5">
                Adaptive memory · {summary.total} vectors · user {userId.slice(0, 8)}...
              </p>
            </div>
          </div>
          <button
            onClick={handleSeedRules}
            disabled={seeding}
            className="rounded-xl bg-emerald-600 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-700 disabled:opacity-60 transition">
            {seeding ? "Seeding…" : seedDone ? "✅ Rules seeded!" : "🌱 Seed ISO 21001 Rules"}
          </button>
        </div>
      </div>

      <main className="mx-auto max-w-5xl px-6 py-8 space-y-6">

        {/* Status */}
        <RagStatus userId={userId} total={summary.total} />

        {/* Tab nav */}
        <div className="flex gap-1 rounded-2xl border border-slate-200 bg-slate-100 p-1 w-fit">
          {([
            { key: "memories",  label: "🧠 Memories"  },
            { key: "context",   label: "🔍 Context Preview" },
            { key: "documents", label: "📄 Knowledge Base" },
          ] as { key: Tab; label: string }[]).map(t => (
            <button key={t.key} onClick={() => setTab(t.key)}
              className={`rounded-xl px-4 py-2 text-xs font-semibold transition ${
                tab === t.key ? "bg-white text-slate-900 shadow-sm" : "text-slate-600 hover:text-slate-900"
              }`}>
              {t.label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        {tab === "memories" && (
          <MemoryList userId={userId} />
        )}

        {tab === "context" && (
          <RagContextPreview userId={userId} />
        )}

        {tab === "documents" && (
          <div className="space-y-6">
            <DocumentUploader onIngest={onIngestDocument} isLoading={ragLoading} />
            <DocumentList />
          </div>
        )}

      </main>
    </div>
  );
}