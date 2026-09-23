// types/notification.ts
// ========================
// Mirrors Services/Notification/notification_schema.py
//
// FIXED to match your actual hooks/useNotifications.ts usage:
// - NotificationSummary has NO "success" field — your EMPTY_SUMMARY literal
//   only has {total, unread, error, warning, info}, so the type now matches
//   exactly (adding "success" here would force you to fill it everywhere).
// - Notification gained an optional status field — onMarkAllRead() in your
//   hook does `{...n, is_read: true, status: "read"}`, so Notification must
//   declare "status" or that assignment fails to typecheck.
//
// Still true from the per-user fix:
// - user_id: string | null (was admin_id: number | null)
// - planning_group_id: string | null added

export type NotifType = "error" | "warning" | "info" | "success";
export type NotificationStatus = "unread" | "read";

export interface Notification {
  id:                number;
  user_id:           string | null;
  planning_group_id: string | null;
  anomaly_id:        number | null;
  notif_type:        NotifType;
  title:             string;
  message:           string;
  is_read:           boolean;
  status?:           NotificationStatus;
  created_at:        string;
}

export interface NotificationSummary {
  total:   number;
  unread:  number;
  error:   number;
  warning: number;
  info:    number;
}