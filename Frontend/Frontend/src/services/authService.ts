// src/services/authService.ts
// ===============================
// Auth via Keycloak (notre backend fait le pont). Pas de formulaire de
// login ici : on redirige vers le backend, qui redirige vers Keycloak,
// qui redirige vers Google/GitHub/son propre login, puis tout revient
// sur /auth/callback (voir src/pages/AuthCallback.tsx).

import { BASE, apiGet } from "./api";
import { clearTokens, getRefreshToken, setTokens } from "../utils/tokenStorage";
import { clearSession, setDisplayName } from "../utils/userStorage";

export interface AuthUser {
  id: string;
  email: string | null;
  display_name: string;
  role: string;
  auth_provider: string;
  avatar_url: string | null;
  is_verified: boolean;
  created_at: string | null;
}

/** Redirige le navigateur vers le backend, qui démarre le flow Keycloak. */
export function login(): void {
  window.location.href = `${BASE}/auth/login`;
}

/** Termine la session côté Keycloak (SSO) et revient sur l'app. */
export function logout(): void {
  clearTokens();
  clearSession();
  window.location.href = `${BASE}/auth/logout`;
}

/** Récupère le profil de l'utilisateur connecté (GET /auth/me) et le met en cache local. */
export async function fetchCurrentUser(): Promise<AuthUser> {
  const user = await apiGet<AuthUser>("/auth/me");
  setDisplayName(user.display_name);
  localStorage.setItem("rag_session_user_id", user.id);
  return user;
}

/** Appelé par AuthCallback juste après la redirection Keycloak. */
export function storeTokensFromCallback(accessToken: string, refreshToken: string): void {
  setTokens(accessToken, refreshToken);
}

/** Rafraîchit l'access_token expiré avec le refresh_token. */
export async function refreshAccessToken(): Promise<void> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) throw new Error("No refresh token stored.");

  const res = await fetch(`${BASE}/auth/refresh?refresh_token=${encodeURIComponent(refreshToken)}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Refresh failed.");

  const data = await res.json();
  setTokens(data.access_token, data.refresh_token);
}