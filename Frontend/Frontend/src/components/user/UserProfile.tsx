// src/components/user/UserProfile.tsx

import { useState }    from "react";
import { useUser }     from "../../hooks/useUser";

export default function UserProfile() {
  const { user, isLoading, error, onUpdate } = useUser();
  const [name,    setName]    = useState("");
  const [editing, setEditing] = useState(false);

  const handleSave = async () => {
    if (!name.trim()) return;
    await onUpdate({ display_name: name.trim() });
    setEditing(false);
  };

  if (isLoading && !user) return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 text-center text-sm text-slate-400">
      Loading profile…
    </div>
  );

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
      <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Your Profile</p>

      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
          ❌ {error}
        </div>
      )}

      <div className="flex items-center gap-4">
        {/* Avatar */}
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-900 text-2xl font-bold text-white">
          {(user?.display_name ?? "A")[0].toUpperCase()}
        </div>

        <div className="flex-1 min-w-0">
          {editing ? (
            <input
              autoFocus
              value={name}
              onChange={e => setName(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleSave()}
              placeholder={user?.display_name}
              className="w-full rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-900 outline-none focus:border-slate-500"
            />
          ) : (
            <p className="text-base font-bold text-slate-900">{user?.display_name ?? "—"}</p>
          )}
          <p className="text-xs text-slate-400 mt-0.5">
            {user?.role ?? "admin"} · ID: {user?.id?.slice(0, 8)}...
          </p>
        </div>

        <div className="flex gap-2">
          {editing ? (
            <>
              <button onClick={handleSave} disabled={isLoading}
                className="rounded-xl bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-slate-800 disabled:opacity-50">
                Save
              </button>
              <button onClick={() => setEditing(false)}
                className="rounded-xl border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600">
                Cancel
              </button>
            </>
          ) : (
            <button onClick={() => { setEditing(true); setName(user?.display_name ?? ""); }}
              className="rounded-xl border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50">
              ✏️ Edit
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 pt-2">
        <div className="rounded-2xl border border-slate-100 bg-slate-50 p-3">
          <p className="text-xs text-slate-500">Status</p>
          <p className="text-sm font-semibold text-emerald-700 mt-0.5">
            {user?.is_active ? "✅ Active" : "❌ Inactive"}
          </p>
        </div>
        <div className="rounded-2xl border border-slate-100 bg-slate-50 p-3">
          <p className="text-xs text-slate-500">Member since</p>
          <p className="text-sm font-semibold text-slate-700 mt-0.5">
            {user?.created_at
              ? new Date(user.created_at).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })
              : "—"}
          </p>
        </div>
      </div>
    </div>
  );
}