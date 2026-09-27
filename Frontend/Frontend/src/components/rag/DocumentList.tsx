// src/components/rag/DocumentList.tsx

import { useEffect } from "react";
import { BookOpen, RefreshCw, Loader2, Inbox } from "lucide-react";
import { useRAG } from "../../hooks/useRAG";
import DocumentItem from "./DocumentItem";

export default function DocumentList() {
  const { documents, isLoading, loadDocuments } = useRAG();

  useEffect(() => { void loadDocuments(); }, [loadDocuments]);

  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      {/* Header */}
      <header className="flex items-center justify-between gap-3 border-b border-slate-100 bg-linear-to-br from-slate-50 via-white to-white px-5 py-4">
        <div className="flex items-center gap-3">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-900 text-white shadow-sm">
            <BookOpen className="h-4 w-4" aria-hidden="true" />
          </span>
          <div>
            <h3 className="text-sm font-semibold tracking-tight text-slate-900">
              Knowledge base
            </h3>
            <p className="text-xs text-slate-500">
              {documents.length} document{documents.length > 1 ? "s" : ""} indexed
            </p>
          </div>
        </div>

        <button
          onClick={() => void loadDocuments()}
          disabled={isLoading}
          className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 transition hover:border-slate-300 hover:bg-slate-50 disabled:opacity-50"
          title="Refresh"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} aria-hidden="true" />
        </button>
      </header>

      {/* Body */}
      <div className="bg-slate-50/40 p-5">
        {isLoading && (
          <div className="flex items-center justify-center gap-2 py-8 text-xs text-slate-500">
            <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
            Loading documents…
          </div>
        )}

        {!isLoading && documents.length === 0 && (
          <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-slate-200 bg-white py-10 text-center">
            <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-50 text-slate-400">
              <Inbox className="h-5 w-5" aria-hidden="true" />
            </span>
            <div className="space-y-1">
              <p className="text-sm font-semibold text-slate-700">No documents yet</p>
              <p className="text-xs text-slate-400">
                Add pedagogical rules or ISO standards above.
              </p>
            </div>
          </div>
        )}

        {!isLoading && documents.length > 0 && (
          <div className="space-y-2">
            {documents.map(doc => (
              <DocumentItem key={doc.id} doc={doc} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}