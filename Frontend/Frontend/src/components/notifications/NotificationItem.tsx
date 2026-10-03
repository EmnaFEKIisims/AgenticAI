// components/notifications/NotificationItem.tsx
// =================================================
// FIX: TYPE_CONFIG only had error/warning/info keys, so any "success"
// notification (backend's NotificationType.SUCCESS — e.g. "no anomalies on
// this new planning version") silently fell back to the "info" style.
// Added a proper "success" entry.

import type { Notification, NotifType } from "../../types/notification";

interface NotificationItemProps {
  notification: Notification;
  onMarkRead:   (id: number) => void;
  onDelete:     (id: number) => void;
}

const TYPE_CONFIG: Record<NotifType, { icon: string; color: string; bg: string }> = {
  error:   { icon: "", color: "text-rose-700",    bg: "bg-rose-50 border-rose-200" },
  warning: { icon: "", color: "text-amber-700",   bg: "bg-amber-50 border-amber-200" },
  info:    { icon: "", color: "text-sky-700",     bg: "bg-sky-50 border-sky-200" },
  success: { icon: "", color: "text-emerald-700", bg: "bg-emerald-50 border-emerald-200" },
};

export default function NotificationItem({ notification, onMarkRead, onDelete }: NotificationItemProps) {
  const cfg = TYPE_CONFIG[notification.notif_type] ?? TYPE_CONFIG.info;

  return (
    <div
      className={`rounded-2xl border p-4 flex items-start gap-3 transition ${cfg.bg} ${
        notification.is_read ? "opacity-60" : ""
      }`}
    >
      <span className="text-lg leading-none">{cfg.icon}</span>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className={`text-sm font-semibold ${cfg.color}`}>{notification.title}</p>
          {!notification.is_read && (
            <span className="h-1.5 w-1.5 rounded-full bg-rose-500" />
          )}
        </div>
        <p className="text-xs text-slate-600 mt-0.5">{notification.message}</p>
        <p className="text-[11px] text-slate-400 mt-1">
          {new Date(notification.created_at).toLocaleString()}
        </p>
      </div>

      <div className="flex flex-col gap-1.5 shrink-0">
        {!notification.is_read && (
          <button
            onClick={() => onMarkRead(notification.id)}
            className="rounded-lg border border-slate-200 bg-white px-2 py-1 text-[11px] font-semibold text-slate-600 hover:bg-slate-50"
          >
            ✓ Read
          </button>
        )}
        <button
          onClick={() => onDelete(notification.id)}
          className="rounded-lg border border-slate-200 bg-white px-2 py-1 text-[11px] font-semibold text-slate-400 hover:bg-slate-50 hover:text-rose-600"
        >
          ✕ Delete
        </button>
      </div>
    </div>
  );
}