// services/notificationService.ts
// ===================================
// FIXED to match the EXACT export names your hooks/useNotifications.ts
// imports (getAllNotifications, getNotificationSummary, markAsRead,
// markAllAsRead, deleteNotification) — previous pass used different names
// and broke the build. Root fix unchanged: goes through apiGet/apiPatch/
// apiDelete from ./api, which sends X-User-ID on every call.

import { apiGet, apiPatch, apiDelete } from "./api";
import type { Notification, NotificationSummary } from "../types/notification";

export async function getAllNotifications(): Promise<Notification[]> {
  return apiGet<Notification[]>("/notifications/");
}

export async function getUnreadNotifications(): Promise<Notification[]> {
  return apiGet<Notification[]>("/notifications/unread");
}

export async function getNotificationSummary(): Promise<NotificationSummary> {
  return apiGet<NotificationSummary>("/notifications/summary");
}

export async function markAsRead(id: number): Promise<Notification> {
  return apiPatch<Notification>(`/notifications/${id}/read`);
}

export async function markAllAsRead(): Promise<{ success: boolean; marked_read: number }> {
  return apiPatch<{ success: boolean; marked_read: number }>("/notifications/read-all");
}

export async function deleteNotification(id: number): Promise<{ success: boolean }> {
  return apiDelete<{ success: boolean }>(`/notifications/${id}`);
}