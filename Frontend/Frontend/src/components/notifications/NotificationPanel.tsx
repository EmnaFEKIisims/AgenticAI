// components/notifications/NotificationPanel.tsx
// Dropdown panel — opened by NotificationBell.

import { useNavigate }   from "react-router-dom";
import type { Notification } from "../../types/notification";
import NotificationItem from "./NotificationItem";

interface NotificationPanelProps {
  notifications: Notification[];
  unreadCount:   number;
  onMarkRead:    (id: number) => void;
  onMarkAllRead: () => void;
  onDelete:      (id: number) => void;
  onClose:       () => void;
}

export default function NotificationPanel({
  notifications, unreadCount,
  onMarkRead, onMarkAllRead, onDelete, onClose,
}: NotificationPanelProps) {
  const navigate = useNavigate();

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 z-40" onClick={onClose} />

      {/* Panel */}
      <div className="absolute right-0 top-12 z-50 w-80 rounded-3xl border border-slate-200 bg-white shadow-xl overflow-hidden">

        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
          <div className="flex items-center gap-2">
            <p className="font-bold text-slate-900 text-sm">Notifications</p>
            {unreadCount > 0 && (
              <span className="rounded-full bg-rose-500 px-2 py-0.5 text-[10px] font-bold text-white">
                {unreadCount}
              </span>
            )}
          </div>
          {unreadCount > 0 && (
            <button onClick={onMarkAllRead}
              className="text-xs text-slate-500 hover:text-slate-700 font-medium">
              Mark all read
            </button>
          )}
        </div>

        {/* List */}
        <div className="max-h-96 overflow-y-auto p-3 space-y-2">
          {notifications.length === 0 ? (
            <div className="py-10 text-center">
              <p className="text-2xl mb-2">🔔</p>
              <p className="text-sm text-slate-500">No notifications yet.</p>
              <p className="text-xs text-slate-400 mt-1">They appear when anomalies are detected.</p>
            </div>
          ) : (
            notifications.slice(0, 10).map(n => (
              <NotificationItem
                key          = {n.id}
                notification = {n}
                onMarkRead   = {onMarkRead}
                onDelete     = {onDelete}
              />
            ))
          )}
        </div>

        {/* Footer */}
        {notifications.length > 0 && (
          <div className="border-t border-slate-100 px-4 py-3">
            <button
              onClick={() => { navigate("/notifications"); onClose(); }}
              className="w-full rounded-xl bg-slate-900 py-2 text-xs font-semibold text-white hover:bg-slate-800"
            >
              View all notifications
            </button>
          </div>
        )}
      </div>
    </>
  );
}