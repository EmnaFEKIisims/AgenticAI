// src/pages/notifications/NotificationsPage.tsx
// REAL FIX this time: the previous file's comment claimed paths were fixed to
// go up 2 levels, but the import statements only went up ONE level (../hooks
// instead of ../../hooks). Since this file lives at
// src/pages/notifications/NotificationsPage.tsx, it needs TWO "../" to reach
// src/hooks, src/components, src/types.

import { useState }                     from "react";
import { useNotifications }             from "../hooks/useNotifications";
import NotificationItem                 from "../components/notifications/NotificationItem";
import type { Notification, NotifType } from "../types/notification";

export default function NotificationsPage() {
  const {
    notifications, summary, isLoading, error,
    refresh, onMarkRead, onMarkAllRead, onDelete,
  } = useNotifications();

  const [filter, setFilter] = useState<NotifType | "all">("all");

  const filtered: Notification[] = filter === "all"
    ? notifications
    : notifications.filter((n: Notification) => n.notif_type === filter);

  return (
    <div className="min-h-screen bg-slate-50">

      {/* Header */}
      <div className="border-b border-slate-200 bg-white px-6 py-4">
        <div className="mx-auto max-w-3xl flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🔔</span>
            <div>
              <h1 className="text-lg font-bold text-slate-900">Notifications</h1>
              <p className="text-xs text-slate-500">
                {summary.unread > 0 ? `${summary.unread} unread` : "All read"}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button onClick={() => void refresh()}
              className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50">
              ↺ Refresh
            </button>
            {summary.unread > 0 && (
              <button onClick={onMarkAllRead}
                className="rounded-xl bg-slate-900 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-800">
                ✓ Mark all read
              </button>
            )}
          </div>
        </div>
      </div>

      <main className="mx-auto max-w-3xl px-6 py-8 space-y-6">

        {/* Summary cards */}
        <div className="grid grid-cols-4 gap-3">
          {(
            [
              { label: "Total",    value: summary.total,   color: "text-slate-700" },
              { label: "Unread",   value: summary.unread,  color: "text-rose-600"  },
              { label: "Errors",   value: summary.error,   color: "text-rose-600"  },
              { label: "Warnings", value: summary.warning, color: "text-amber-600" },
            ] as { label: string; value: number; color: string }[]
          ).map(({ label, value, color }) => (
            <div key={label} className="rounded-2xl border border-slate-200 bg-white p-4 text-center">
              <p className={`text-2xl font-bold ${color}`}>{value}</p>
              <p className="text-xs text-slate-500 mt-0.5">{label}</p>
            </div>
          ))}
        </div>

        {/* Filters */}
        <div className="flex gap-2 flex-wrap">
          {(["all", "error", "warning", "info", "success"] as (NotifType | "all")[]).map(f => (
            <button key={f} onClick={() => setFilter(f)}
              className={`rounded-xl px-4 py-1.5 text-xs font-semibold transition ${
                filter === f
                  ? "bg-slate-900 text-white"
                  : "border border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
              }`}>
              {f === "all"     && "All"}
              {f === "error"   && "🔴 Errors"}
              {f === "warning" && "🟡 Warnings"}
              {f === "info"    && "🔵 Info"}
              {f === "success" && "🟢 Success"}
            </button>
          ))}
        </div>

        {/* Error */}
        {error && (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
            ❌ {error}
          </div>
        )}

        {/* Loading */}
        {isLoading && (
          <div className="py-10 text-center text-sm text-slate-400">
            Loading notifications…
          </div>
        )}

        {/* List */}
        {!isLoading && (
          <div className="space-y-3">
            {filtered.length === 0 ? (
              <div className="rounded-3xl border border-slate-200 bg-white p-10 text-center">
                <p className="text-3xl mb-3">🔔</p>
                <p className="text-sm font-semibold text-slate-700">No notifications</p>
                <p className="text-xs text-slate-400 mt-1">
                  Notifications appear when the Anomaly Agent detects issues.
                </p>
              </div>
            ) : (
              filtered.map((n: Notification) => (
                <NotificationItem
                  key          = {n.id}
                  notification = {n}
                  onMarkRead   = {onMarkRead}
                  onDelete     = {onDelete}
                />
              ))
            )}
          </div>
        )}

      </main>
    </div>
  );
}