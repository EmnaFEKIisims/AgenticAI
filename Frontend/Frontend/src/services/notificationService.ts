/// <reference types="vite/client" />
// src/services/notificationService.ts

import type { Notification, NotificationSummary } from "../types/notification";

// Fixed: vite/client reference added above → no more 'env' error
const BASE = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "")
           ?? "http://localhost:8000";

async function call<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try { const b = await res.json(); detail = b?.detail ?? detail; } catch {}
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

// GET /notifications
export const getAllNotifications = (limit = 50): Promise<Notification[]> =>
  call(`/notifications?limit=${limit}`);

// GET /notifications/unread
export const getUnreadNotifications = (): Promise<Notification[]> =>
  call("/notifications/unread");

// GET /notifications/summary
export const getNotificationSummary = (): Promise<NotificationSummary> =>
  call("/notifications/summary");

// PATCH /notifications/{id}/read
export const markAsRead = (id: number): Promise<Notification> =>
  call(`/notifications/${id}/read`, { method: "PATCH" });

// PATCH /notifications/read-all
export const markAllAsRead = (): Promise<{ success: boolean; marked_read: number }> =>
  call("/notifications/read-all", { method: "PATCH" });

// DELETE /notifications/{id}
export const deleteNotification = (id: number): Promise<{ success: boolean }> =>
  call(`/notifications/${id}`, { method: "DELETE" });