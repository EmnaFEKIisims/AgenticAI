/// <reference types="vite/client" />
// src/services/api.ts
// ===================
// Single centralized fetch function used by ALL services.
//
// What it does automatically:
//   Adds X-User-ID header        → backend knows which user
//   Adds Content-Type: application/json
//   Handles errors uniformly
//   🔜 Will add Authorization: Bearer (after Keycloak)

const SUPERADMIN_ID = "00000000-0000-0000-0000-000000000001";

export const BASE = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "")
                  ?? "http://localhost:8000";

function getUserId(): string {
  return localStorage.getItem("rag_session_user_id") ?? SUPERADMIN_ID;
}

// ── Main fetch helper ─────────────────────────────────────────────────────────

export async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const headers = new Headers(options.headers);

  // Always set user identity (before Keycloak: from localStorage)
  headers.set("X-User-ID", getUserId());

  // JSON by default (overridden for FormData in uploadFile)
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  // After Keycloak: uncomment these lines
  // if (keycloak.authenticated && keycloak.token) {
  //   headers.set("Authorization", `Bearer ${keycloak.token}`);
  // }

  const url = path.startsWith("http") ? path : `${BASE}${path}`;

  let res: Response;
  try {
    res = await fetch(url, { ...options, headers });
  } catch {
    throw new Error(
      `Cannot reach backend at ${BASE}. ` +
      `Make sure uvicorn is running: uvicorn main:app --reload`
    );
  }

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try { const b = await res.json(); detail = b?.detail ?? detail; } catch {}
    throw new Error(detail);
  }

  return res;
}

// ── Typed shortcuts ───────────────────────────────────────────────────────────

export async function apiGet<T>(path: string): Promise<T> {
  const res = await apiFetch(path);
  return res.json() as Promise<T>;
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const res = await apiFetch(path, {
    method: "POST",
    body:   body !== undefined ? JSON.stringify(body) : undefined,
  });
  return res.json() as Promise<T>;
}

export async function apiPut<T>(path: string, body: unknown): Promise<T> {
  const res = await apiFetch(path, { method: "PUT", body: JSON.stringify(body) });
  return res.json() as Promise<T>;
}

export async function apiPatch<T>(path: string, body?: unknown): Promise<T> {
  const res = await apiFetch(path, {
    method: "PATCH",
    body:   body !== undefined ? JSON.stringify(body) : undefined,
  });
  return res.json() as Promise<T>;
}

export async function apiDelete<T = { success: boolean }>(path: string): Promise<T> {
  const res = await apiFetch(path, { method: "DELETE" });
  return res.json() as Promise<T>;
}