// src/types/user.ts

export type UserRole = "admin" | "trainer" | "viewer";

export interface User {
  id:           string;
  display_name: string;
  role:         UserRole;
  is_active:    boolean;
  created_at:   string | null;
  last_seen_at: string | null;
}

export interface UserCreate {
  id:           string;
  display_name?: string;
  role?:         UserRole;
}

export interface UserUpdate {
  display_name?: string;
  role?:         UserRole;
}