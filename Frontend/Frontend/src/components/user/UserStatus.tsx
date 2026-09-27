// src/components/user/UserStatus.tsx
// Compact badge for the navbar — shows user identity.

import { useUser } from "../../hooks/useUser";

export default function UserStatus() {
  const { user, userId } = useUser();

  return (
    <div className="flex items-center gap-2.5 rounded-xl border border-slate-200 bg-white px-3 py-1.5 shadow-sm transition hover:border-slate-300">
      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-linear-to-br from-slate-800 to-slate-900 text-xs font-bold text-white shadow-sm">
        {(user?.display_name ?? "A")[0].toUpperCase()}
      </div>

      <div className="min-w-0 leading-tight">
        <p className="truncate text-xs font-semibold text-slate-800">
          {user?.display_name ?? "Administrator"}
        </p>
        <p className="truncate font-mono text-[10px] text-slate-400">
          {userId.slice(0, 8)}
        </p>
      </div>

      <span
        className="h-2 w-2 shrink-0 rounded-full bg-emerald-500 ring-2 ring-emerald-100"
        title="Active session"
      />
    </div>
  );
}