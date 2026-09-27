// src/pages/rag/RagPage.tsx

import { useState } from "react";
import {
  Brain,
  Search,
  FileText,
  Database,
  Sprout,
  CheckCircle2,
  Loader2,
} from "lucide-react";
import { useUser }       from "../hooks/useUser";
import { useMemory }     from "../hooks/useMemory";
import { useRAG }        from "../hooks/useRAG";
import RagStatus         from "../components/rag/RagStatus";
import MemoryList        from "../components/rag/MemoryList";
import RagContextPreview from "../components/rag/RagContextPreview";
import DocumentUploader  from "../components/rag/DocumentUploader";
import DocumentList      from "../components/rag/DocumentList";

type Tab = "memories" | "context" | "documents";

const TAB_CONFIG: {
  key: Tab;
  label: string;
  Icon: React.ElementType;
}[] = [
  { key: "memories",  label: "Memories",          Icon: Brain },
  { key: "context",   label: "Context preview",   Icon: Search },
  { key: "documents", label: "Knowledge base",    Icon: FileText },
];

export default function RagPage() {
  const { userId } = useUser();
  const { summary } = useMemory(userId);
  const { isLoading: ragLoading, onIngestDocument, onSeedRules } = useRAG();
  const [tab,      setTab]      = useState<Tab>("memories");
  const [seeding,  setSeeding]  = useState(false);
  const [seedDone, setSeedDone] = useState(false);

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
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-6 py-5">
          <div className="flex min-w-0 items-center gap-4">
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-slate-900 text-white shadow-sm">
              <Brain className="h-5 w-5" aria-hidden="true" />
            </span>
            <div className="min-w-0">
              <h1 className="text-lg font-semibold tracking-tight text-slate-900">
                RAG Memory · Qdrant
              </h1>
              <div className="mt-0.5 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                <span className="inline-flex items-center gap-1.5">
                  <Database className="h-3 w-3 text-slate-400" aria-hidden="true" />
                  Adaptive memory
                </span>
                <span className="h-3 w-px bg-slate-200" />
                <span className="font-mono">
                  {summary.total} vectors
                </span>
                <span className="h-3 w-px bg-slate-200" />
                <span className="font-mono text-slate-400">
                  user {userId.slice(0, 8)}
                </span>
              </div>
            </div>
          </div>

          <button
            onClick={handleSeedRules}
            disabled={seeding}
            className="inline-flex shrink-0 items-center gap-2 rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-700 hover:shadow disabled:cursor-not-allowed disabled:opacity-60"
          >
            {seeding ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
                Seeding…
              </>
            ) : seedDone ? (
              <>
                <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
                Rules seeded
              </>
            ) : (
              <>
                <Sprout className="h-3.5 w-3.5" aria-hidden="true" />
                Seed ISO 21001 rules
              </>
            )}
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-5xl space-y-6 px-6 py-8">
        {/* Status */}
        <RagStatus userId={userId} total={summary.total} />

        {/* Tab navigation */}
        <div className="flex w-fit gap-1 rounded-2xl border border-slate-200 bg-slate-100 p-1">
          {TAB_CONFIG.map(t => {
            const Icon = t.Icon;
            const isActive = tab === t.key;
            return (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition ${
                  isActive
                    ? "bg-white text-slate-900 shadow-sm"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                <Icon className="h-3.5 w-3.5" aria-hidden="true" />
                {t.label}
              </button>
            );
          })}
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