/// <reference types="vite/client" />
// src/services/userService.ts

import type { User, UserCreate, UserUpdate } from "../types/user";

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

// POST /users/register — create or update user from localStorage UUID
export const registerUser = (body: UserCreate): Promise<User> =>
  call("/users/register", { method: "POST", body: JSON.stringify(body) });

// GET /users/{id}
export const getUser = (userId: string): Promise<User> =>
  call(`/users/${userId}`);

// PUT /users/{id}
export const updateUser = (userId: string, body: UserUpdate): Promise<User> =>
  call(`/users/${userId}`, { method: "PUT", body: JSON.stringify(body) });

// GET /users
export const listUsers = (): Promise<User[]> =>
  call("/users");