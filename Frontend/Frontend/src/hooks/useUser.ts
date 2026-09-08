// src/hooks/useUser.ts

import { useState, useEffect, useCallback } from "react";
import type { User, UserUpdate }             from "../types/user";
import { registerUser, updateUser }          from "../services/userService";
import { getOrCreateUserId, getDisplayName, setDisplayName } from "../utils/userStorage";

interface UseUserReturn {
  user:       User | null;
  userId:     string;
  isLoading:  boolean;
  error:      string | null;
  onUpdate:   (body: UserUpdate) => Promise<void>;
}

export function useUser(): UseUserReturn {
  const [user,      setUser]      = useState<User | null>(null);
  const [userId,    setUserId]    = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error,     setError]     = useState<string | null>(null);

  useEffect(() => {
    const id   = getOrCreateUserId();
    const name = getDisplayName();
    setUserId(id);
    setIsLoading(true);
    registerUser({ id, display_name: name })
      .then(u => setUser(u))
      .catch(e => setError(e instanceof Error ? e.message : "Registration failed"))
      .finally(() => setIsLoading(false));
  }, []);

  const onUpdate = useCallback(async (body: UserUpdate) => {
    if (!userId) return;
    setIsLoading(true); setError(null);
    try {
      const updated = await updateUser(userId, body);
      setUser(updated);
      if (body.display_name) setDisplayName(body.display_name);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Update failed");
    } finally {
      setIsLoading(false);
    }
  }, [userId]);

  return { user, userId, isLoading, error, onUpdate };
}