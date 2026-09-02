// src/components/rag/DocumentUploader.tsx
// Paste or upload text to add to the Qdrant knowledge base.

import { useState } from "react";

interface Props {
  onIngest:  (title: string, source: string, content: string) => Promise<void>;
  isLoading: boolean;
}

export default function DocumentUploader({ onIngest, isLoading }: Props) {
  const [title,   setTitle]   = useState("");
  const [source,  setSource]  = useState("ISO 21001:2018");
  const [content, setContent] = useState("");
  const [done,    setDone]    = useState(false);

  const handleSubmit = async () => {
    if (!title.trim() || !content.trim()) return;
    await onIngest(title, source, content);
    setTitle(""); setSource("ISO 21001:2018"); setContent("");
    setDone(true);
    setTimeout(() => setDone(false), 3000);
  };

  if (done) return (
    <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-center text-sm font-semibold text-emerald-700">
      ✅ Document indexed into Qdrant knowledge base.
    </div>
  );

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm space-y-3">
      <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
        📄 Add Knowledge Document
      </p>
      <p className="text-xs text-slate-400">
        Paste pedagogical rules, ISO standards, or guidelines. They'll be chunked, embedded, and stored in Qdrant.
      </p>

      <input value={title} onChange={e => setTitle(e.target.value)}
        placeholder="Document title (e.g. ISO 21001 Training Rules)"
        className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800 outline-none focus:border-slate-400" />

      <input value={source} onChange={e => setSource(e.target.value)}
        placeholder="Source (e.g. ISO 21001:2018)"
        className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800 outline-none focus:border-slate-400" />

      <textarea value={content} onChange={e => setContent(e.target.value)}
        placeholder="Paste the full text of the document here..."
        rows={6}
        className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800 outline-none focus:border-slate-400 resize-none" />

      <button onClick={handleSubmit} disabled={!title.trim() || !content.trim() || isLoading}
        className="w-full rounded-xl bg-slate-900 py-2.5 text-xs font-semibold text-white hover:bg-slate-800 disabled:opacity-50 transition">
        {isLoading ? "Indexing into Qdrant…" : "Index Document"}
      </button>
    </div>
  );
}