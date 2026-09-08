// src/utils/userStorage.ts
// Manages the anonymous session UUID in localStorage.
// This UUID is the user identity for RAG memory — no login needed.

const SESSION_KEY    = "rag_session_user_id";
const DISPLAY_KEY    = "rag_display_name";

export function getOrCreateUserId(): string {
  let id = localStorage.getItem(SESSION_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(SESSION_KEY, id);
  }
  return id;
}

export function getUserId(): string | null {
  return localStorage.getItem(SESSION_KEY);
}

export function getDisplayName(): string {
  return localStorage.getItem(DISPLAY_KEY) ?? "Administrator";
}

export function setDisplayName(name: string): void {
  localStorage.setItem(DISPLAY_KEY, name);
}

export function clearSession(): void {
  localStorage.removeItem(SESSION_KEY);
  localStorage.removeItem(DISPLAY_KEY);
}