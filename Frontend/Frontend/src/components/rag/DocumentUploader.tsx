// src/components/rag/DocumentUploader.tsx
// Add useful planning guidance.

import { useState } from "react";
import { FilePlus2, CheckCircle2, Loader2, Send, FileText } from "lucide-react";

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

  if (done) {
    return (
      <div className="flex items-center gap-3 rounded-2xl border border-emerald-100 bg-emerald-50/70 px-5 py-4 shadow-sm">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white text-emerald-600 shadow-sm">
          <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
        </span>
        <div>
          <p className="text-sm font-semibold text-emerald-800">Guidance saved</p>
            <p className="text-xs text-emerald-700/80">It will be considered in future plans.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      {/* Header */}
      <header className="flex items-start gap-3 border-b border-slate-100 bg-linear-to-br from-slate-50 via-white to-white px-5 py-4">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-900 text-white shadow-sm">
          <FilePlus2 className="h-4 w-4" aria-hidden="true" />
        </span>
        <div className="min-w-0">
          <h3 className="text-sm font-semibold tracking-tight text-slate-900">
            Add planning guidance
          </h3>
          <p className="mt-0.5 text-xs text-slate-500">
            Add a note, rule, or guideline to consider when plans are prepared.
          </p>
        </div>
      </header>

      {/* Body */}
      <div className="space-y-3 bg-slate-50/40 p-5">
        <div className="space-y-1.5">
          <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
            Name
          </label>
          <input
            value={title}
            onChange={e => setTitle(e.target.value)}
            placeholder="e.g. Practical training guidelines"
            className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 outline-none transition focus:border-slate-400 focus:ring-2 focus:ring-slate-100"
          />
        </div>

        <div className="space-y-1.5">
          <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
            Where it comes from
          </label>
          <input
            value={source}
            onChange={e => setSource(e.target.value)}
            placeholder="e.g. Training handbook"
            className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 outline-none transition focus:border-slate-400 focus:ring-2 focus:ring-slate-100"
          />
        </div>

        <div className="space-y-1.5">
          <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
            Guidance
          </label>
          <textarea
            value={content}
            onChange={e => setContent(e.target.value)}
            placeholder="Write or paste the guidance here…"
            rows={6}
            className="w-full resize-none rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 outline-none transition focus:border-slate-400 focus:ring-2 focus:ring-slate-100"
          />
        </div>

        <div className="flex items-center justify-between gap-3 pt-1">
          <p className="text-[11px] text-slate-400">
            <FileText className="mr-1 inline h-3 w-3" aria-hidden="true" />
            {content.length} characters
          </p>

          <button
            onClick={handleSubmit}
            disabled={!title.trim() || !content.trim() || isLoading}
            className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 hover:shadow disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
                Saving…
              </>
            ) : (
              <>
                <Send className="h-3.5 w-3.5" aria-hidden="true" />
                Save guidance
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}