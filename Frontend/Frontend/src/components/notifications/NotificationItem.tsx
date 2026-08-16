// components/notifications/NotificationItem.tsx

import { useNavigate } from "react-router-dom";
import type { Notification } from "../../types/notification";

interface NotificationItemProps {
  notification: Notification;
  onMarkRead:   (id: number) => void;
  onDelete:     (id: number) => void;
}

const TYPE_CONFIG = {
  error:   { icon: "🔴", bg: "bg-rose-50   border-rose-100",   text: "text-rose-800"   },
  warning: { icon: "🟡", bg: "bg-amber-50  border-amber-100",  text: "text-amber-800"  },
  info:    { icon: "🔵", bg: "bg-sky-50    border-sky-100",    text: "text-sky-800"    },
};

export default function NotificationItem({ notification, onMarkRead, onDelete }: NotificationItemProps) {
  const navigate = useNavigate();
  const cfg      = TYPE_CONFIG[notification.notif_type] ?? TYPE_CONFIG.info;

  const handleClick = () => {
    if (!notification.is_read) onMarkRead(notification.id);
    if (notification.action_url) navigate(notification.action_url);
  };

  const timeAgo = (iso: string | null) => {
    if (!iso) return "";
    const diff = Date.now() - new Date(iso).getTime();
    const m    = Math.floor(diff / 60000);
    if (m < 1)  return "just now";
    if (m < 60) return `${m}m ago`;
    const h = Math.floor(m / 60);
    if (h < 24) return `${h}h ago`;
    return `${Math.floor(h / 24)}d ago`;
  };

  return (
    <div
      onClick={handleClick}
      className={`relative flex gap-3 rounded-xl border p-3 cursor-pointer transition hover:shadow-sm ${cfg.bg} ${!notification.is_read ? "ring-2 ring-offset-1 ring-rose-200" : "opacity-70"}`}
    >
      <span className="text-lg shrink-0">{cfg.icon}</span>

      <div className="flex-1 min-w-0">
        <p className={`text-xs font-bold leading-snug ${cfg.text}`}>{notification.title}</p>
        <p className="text-xs text-slate-600 mt-0.5 line-clamp-2">{notification.message}</p>
        <p className="text-[10px] text-slate-400 mt-1">{timeAgo(notification.created_at)}</p>
      </div>

      {/* Delete button */}
      <button
        onClick={e => { e.stopPropagation(); onDelete(notification.id); }}
        className="shrink-0 self-start text-slate-300 hover:text-slate-500 text-xs font-bold"
      >
        ✕
      </button>
    </div>
  );
}