// components/notifications/NotificationBadge.tsx
// Red badge showing unread count — used on the bell icon.

interface NotificationBadgeProps { count: number; }

export default function NotificationBadge({ count }: NotificationBadgeProps) {
  if (count === 0) return null;
  return (
    <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-rose-500 text-[10px] font-bold text-white shadow-sm">
      {count > 99 ? "99+" : count}
    </span>
  );
}