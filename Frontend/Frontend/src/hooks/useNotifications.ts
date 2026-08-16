// src/hooks/useNotifications.ts
// Import path: ../services/notificationService
// (hooks/ and services/ are both inside src/)

import { useState, useEffect, useCallback } from "react";
import type { Notification, NotificationSummary } from "../types/notification";
import {
  getAllNotifications,
  getNotificationSummary,
  markAsRead,
  markAllAsRead,
  deleteNotification,
} from "../services/notificationService";   // ← correct: hooks → ../services

const POLL_INTERVAL_MS = 30_000; // 30 seconds

interface UseNotificationsReturn {
  notifications:  Notification[];
  summary:        NotificationSummary;
  isLoading:      boolean;
  isOpen:         boolean;
  error:          string | null;
  setIsOpen:      (v: boolean) => void;
  refresh:        () => Promise<void>;
  onMarkRead:     (id: number) => Promise<void>;
  onMarkAllRead:  () => Promise<void>;
  onDelete:       (id: number) => Promise<void>;
}

const EMPTY_SUMMARY: NotificationSummary = {
  total: 0, unread: 0, error: 0, warning: 0, info: 0,
};

export function useNotifications(): UseNotificationsReturn {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [summary,       setSummary]       = useState<NotificationSummary>(EMPTY_SUMMARY);
  const [isLoading,     setIsLoading]     = useState(false);
  const [isOpen,        setIsOpen]        = useState(false);
  const [error,         setError]         = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    try {
      const [notifs, sum] = await Promise.all([
        getAllNotifications(),
        getNotificationSummary(),
      ]);
      setNotifications(notifs);
      setSummary(sum);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load notifications");
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Initial load + polling every 30s
  useEffect(() => {
    void refresh();
    const interval = setInterval(() => void refresh(), POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [refresh]);

  const onMarkRead = useCallback(async (id: number) => {
    try {
      const updated = await markAsRead(id);
      setNotifications(prev => prev.map(n => n.id === id ? updated : n));
      setSummary(prev => ({ ...prev, unread: Math.max(0, prev.unread - 1) }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to mark as read");
    }
  }, []);

  const onMarkAllRead = useCallback(async () => {
    try {
      await markAllAsRead();
      setNotifications(prev =>
        prev.map(n => ({ ...n, is_read: true, status: "read" as const }))
      );
      setSummary(prev => ({ ...prev, unread: 0 }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to mark all as read");
    }
  }, []);

  const onDelete = useCallback(async (id: number) => {
    try {
      await deleteNotification(id);
      setNotifications(prev => {
        const removed = prev.find(n => n.id === id);
        const next    = prev.filter(n => n.id !== id);
        setSummary(s => ({
          ...s,
          total:  s.total - 1,
          unread: removed && !removed.is_read ? Math.max(0, s.unread - 1) : s.unread,
        }));
        return next;
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete notification");
    }
  }, []);

  return {
    notifications, summary, isLoading, isOpen, error,
    setIsOpen, refresh, onMarkRead, onMarkAllRead, onDelete,
  };
}