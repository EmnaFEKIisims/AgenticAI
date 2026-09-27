// src/components/user/UserProfile.tsx

import { useState } from "react";
import {
  User as UserIcon,
  Pencil,
  Check,
  X,
  AlertCircle,
  ShieldCheck,
  CalendarDays,
  Loader2,
} from "lucide-react";
import { useUser } from "../../hooks/useUser";

export default function UserProfile() {
  const { user, isLoading, error, onUpdate } = useUser();
  const [name, setName] = useState("");
  const [editing, setEditing] = useState(false);

  const handleSave = async () => {
    if (!name.trim()) return;
    await onUpdate({ display_name: name.trim() });
    setEditing(false);
  };

  if (isLoading && !user) {
    return (
      <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
          <Loader2 className="h-6 w-6 animate-spin text-slate-400" aria-hidden="true" />
          <p className="text-sm text-slate-500">Loading profile…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      {/* Header */}
      <header className="flex items-center gap-3 border-b border-slate-100 bg-linear-to-br from-slate-50 via-white to-white px-6 py-5">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-900 text-white shadow-sm">
          <UserIcon className="h-4 w-4" aria-hidden="true" />
        </span>
        <div>
          <h2 className="text-sm font-semibold tracking-tight text-slate-900">
            Your profile
          </h2>
          <p className="text-xs text-slate-500">
            Manage your identity and account details.
          </p>
        </div>
      </header>

      {/* Body */}
      <div className="space-y-5 bg-slate-50/40 p-6">
        {error && (
          <div className="flex items-start gap-2.5 rounded-xl border border-rose-100 bg-rose-50/70 px-3.5 py-3">
            <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-rose-600" aria-hidden="true" />
            <p className="text-xs text-rose-800">{error}</p>
          </div>
        )}

        {/* Identity card */}
        <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-4">
            {/* Avatar */}
            <div className="relative flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-linear-to-br from-slate-800 to-slate-900 text-xl font-bold text-white shadow-md">
              {(user?.display_name ?? "A")[0].toUpperCase()}
              <span
                className={`absolute -bottom-1 -right-1 h-4 w-4 rounded-full border-2 border-white ${
                  user?.is_active ? "bg-emerald-500" : "bg-slate-300"
                }`}
                title={user?.is_active ? "Active" : "Inactive"}
              />
            </div>

            {/* Info / Edit */}
            <div className="min-w-0 flex-1">
              {editing ? (
                <input
                  autoFocus
                  value={name}
                  onChange={e => setName(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && handleSave()}
                  placeholder={user?.display_name}
                  className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-900 outline-none transition focus:border-slate-400 focus:ring-2 focus:ring-slate-100"
                />
              ) : (
                <p className="truncate text-base font-semibold text-slate-900">
                  {user?.display_name ?? "—"}
                </p>
              )}
              <div className="mt-1 flex items-center gap-2 text-xs text-slate-500">
                <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 font-medium text-slate-600">
                  <ShieldCheck className="h-3 w-3 text-slate-500" aria-hidden="true" />
                  {user?.role ?? "admin"}
                </span>
                <span className="font-mono text-[11px] text-slate-400">
                  ID · {user?.id?.slice(0, 8)}
                </span>
              </div>
            </div>

            {/* Actions */}
            <div className="flex shrink-0 gap-2">
              {editing ? (
                <>
                  <button
                    onClick={handleSave}
                    disabled={isLoading}
                    className="inline-flex items-center gap-1.5 rounded-xl bg-slate-900 px-3.5 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <Check className="h-3 w-3" aria-hidden="true" />
                    Save
                  </button>
                  <button
                    onClick={() => setEditing(false)}
                    className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-600 transition hover:border-slate-300 hover:bg-slate-50"
                  >
                    <X className="h-3 w-3" aria-hidden="true" />
                    Cancel
                  </button>
                </>
              ) : (
                <button
                  onClick={() => {
                    setEditing(true);
                    setName(user?.display_name ?? "");
                  }}
                  className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50 hover:shadow-sm"
                >
                  <Pencil className="h-3 w-3" aria-hidden="true" />
                  Edit
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
            <div className="flex items-center gap-2">
              <span
                className={`flex h-7 w-7 items-center justify-center rounded-lg ${
                  user?.is_active
                    ? "bg-emerald-50 text-emerald-600"
                    : "bg-slate-100 text-slate-500"
                }`}
              >
                <Check className="h-3.5 w-3.5" aria-hidden="true" />
              </span>
              <p className="text-xs font-medium text-slate-500">Status</p>
            </div>
            <p
              className={`mt-2.5 text-sm font-semibold ${
                user?.is_active ? "text-emerald-700" : "text-slate-600"
              }`}
            >
              {user?.is_active ? "Active" : "Inactive"}
            </p>
          </div>

          <div className="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
            <div className="flex items-center gap-2">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-slate-100 text-slate-500">
                <CalendarDays className="h-3.5 w-3.5" aria-hidden="true" />
              </span>
              <p className="text-xs font-medium text-slate-500">Member since</p>
            </div>
            <p className="mt-2.5 text-sm font-semibold text-slate-700">
              {user?.created_at
                ? new Date(user.created_at).toLocaleDateString("en-GB", {
                    day: "numeric",
                    month: "short",
                    year: "numeric",
                  })
                : "—"}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}