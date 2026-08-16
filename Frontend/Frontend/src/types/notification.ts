// types/notification.ts
// ======================

export type NotifType   = "error" | "warning" | "info";
export type NotifStatus = "unread" | "read";

export interface Notification {
  id:         number;
  anomaly_id: number | null;
  admin_id:   number | null;
  notif_type: NotifType;
  status:     NotifStatus;
  title:      string;
  message:    string;
  action_url: string | null;
  is_read:    boolean;
  read_at:    string | null;
  created_at: string | null;
}

export interface NotificationSummary {
  total:   number;
  unread:  number;
  error:   number;
  warning: number;
  info:    number;
}