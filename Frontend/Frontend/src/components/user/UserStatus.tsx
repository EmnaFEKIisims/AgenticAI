// src/components/user/UserStatus.tsx
// Compact badge for the navbar — shows user identity.

import { useUser } from "../../hooks/useUser";

export default function UserStatus() {
  const { user, userId } = useUser();

  return (
    <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-1.5">
      <div className="w-6 h-6 rounded-lg bg-slate-800 flex items-center justify-center text-xs text-white font-bold">
        {(user?.display_name ?? "A")[0].toUpperCase()}
      </div>
      <div className="leading-tight">
        <p className="text-xs font-semibold text-slate-800">
          {user?.display_name ?? "Administrator"}
        </p>
        <p className="text-[10px] text-slate-400">{userId.slice(0, 8)}...</p>
      </div>
      <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0" title="Active session" />
    </div>
  );
}