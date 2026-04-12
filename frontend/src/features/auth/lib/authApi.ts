/** Auth API client — token management and backend calls. */

import type { User } from "../types/auth";

const AUTH_BASE = "/api/v1/auth";
const TOKEN_KEY = "auth_token";

// ── Token storage ───────────────────────────────────────────────────

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

// ── API calls ───────────────────────────────────────────────────────

export async function fetchCurrentUser(): Promise<User | null> {
  const token = getToken();
  if (!token) return null;

  const res = await fetch(`${AUTH_BASE}/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) {
    if (res.status === 401 || res.status === 403) clearToken();
    return null;
  }

  return res.json();
}

export interface DevTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export async function requestDevToken(
  email: string,
  password: string,
): Promise<DevTokenResponse> {
  const params = new URLSearchParams({ email, password });

  const res = await fetch(`${AUTH_BASE}/dev-token?${params.toString()}`, {
    method: "POST",
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(
      body?.detail ?? `Error al obtener token: ${res.statusText}`,
    );
  }

  return res.json();
}
