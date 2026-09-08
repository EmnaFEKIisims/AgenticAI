// src/components/rag/DocumentList.tsx

import { useEffect }        from "react";
import { useRAG }           from "../../hooks/useRAG";
import DocumentItem         from "./DocumentItem";

export default function DocumentList() {
  const { documents, isLoading, loadDocuments } = useRAG();

  useEffect(() => { void loadDocuments(); }, [loadDocuments]);

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
          Knowledge Base ({documents.length} documents)
        </p>
        <button onClick={() => void loadDocuments()}
          className="rounded-xl border border-slate-200 px-3 py-1 text-xs text-slate-600 hover:bg-slate-50">
          ↺
        </button>
      </div>

      {isLoading && (
        <p className="text-xs text-slate-400 text-center py-4">Loading…</p>
      )}

      {!isLoading && documents.length === 0 && (
        <div className="rounded-2xl border border-slate-100 bg-slate-50 p-6 text-center">
          <p className="text-2xl mb-2">📚</p>
          <p className="text-xs font-semibold text-slate-600">No documents yet</p>
          <p className="text-xs text-slate-400 mt-1">
            Add pedagogical rules or ISO standards above.
          </p>
        </div>
      )}

      <div className="space-y-2">
        {documents.map(doc => (
          <DocumentItem key={doc.id} doc={doc} />
        ))}
      </div>
    </div>
  );
}