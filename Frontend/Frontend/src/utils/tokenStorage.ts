// src/utils/tokenStorage.ts
// ===========================
// Stockage des tokens Keycloak (access_token / refresh_token) dans localStorage.
// Fichier séparé de api.ts et authService.ts pour éviter les imports circulaires
// (api.ts a besoin du token, authService.ts a besoin de api.ts pour BASE).

const ACCESS_TOKEN_KEY  = "auth_access_token";
const REFRESH_TOKEN_KEY = "auth_refresh_token";

export function setTokens(accessToken: string, refreshToken: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export function isAuthenticated(): boolean {
  return !!getAccessToken();
}