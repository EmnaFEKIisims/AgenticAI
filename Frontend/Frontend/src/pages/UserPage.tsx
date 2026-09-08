// src/pages/user/UserPage.tsx

import { BrainCircuit } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useUser } from "../hooks/useUser";
import { useMemory } from "../hooks/useMemory";
import UserProfile from "../components/user/UserProfile";
import RagStatus from "../components/rag/RagStatus";

export default function UserPage() {
  const navigate = useNavigate();
  const { userId } = useUser();
  const { summary } = useMemory(userId);

  return (
    <div className="min-h-screen bg-slate-50">

      {/* Header */}
      <div className="border-b border-slate-200 bg-white px-6 py-5">
        <div className="mx-auto flex max-w-3xl items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold text-slate-900">👤 Profile & Identity</h1>
            <p className="mt-1 text-xs text-slate-500">
              Your anonymous session — no login required.
              This identity links your planning preferences stored in Qdrant.
            </p>
          </div>

          <button
            type="button"
            onClick={() => navigate("/rag")}
            className="flex h-11 w-11 items-center justify-center rounded-full bg-violet-600 text-white shadow-sm transition hover:bg-violet-700"
            aria-label="Open RAG page"
            title="Open RAG page"
          >
            <BrainCircuit size={18} aria-hidden="true" />
          </button>
        </div>
      </div>

      <main className="mx-auto max-w-3xl px-6 py-8 space-y-6">

        {/* Profile card */}
        <UserProfile />

        {/* RAG Status */}
        <RagStatus userId={userId} total={summary.total} />

        {/* How identity works */}
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
            How your identity works
          </p>
          <div className="space-y-3">
            {[
              { icon: "🔑", title: "Anonymous UUID", desc: "A unique ID is generated on your first visit and stored in your browser's localStorage. No email, no password." },
              { icon: "🧠", title: "Linked to memories", desc: "Every preference, decision, and feedback is tagged with your UUID in Qdrant. Only your memories are retrieved for your plannings." },
              { icon: "🔒", title: "Private", desc: "Your memories are never shared with other users. Clearing your browser localStorage removes your identity." },
            ].map(({ icon, title, desc }) => (
              <div key={title} className="flex gap-3 rounded-2xl border border-slate-100 bg-slate-50 p-4">
                <span className="text-xl shrink-0">{icon}</span>
                <div>
                  <p className="text-sm font-semibold text-slate-800">{title}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

      </main>
    </div>
  );
}