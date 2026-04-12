"use client";

/**
 * useAuth — manages authentication state.
 *
 * Provides:
 *   - user: current authenticated user or null
 *   - isLoading: true while checking session
 *   - login(): redirect to Google OAuth
 *   - logout(): clear session and redirect to /login
 *
 * TODO: implement with next-auth or custom OAuth flow
 */

import { useCallback, useState } from "react";
import type { User } from "../types/auth";

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const login = useCallback(() => {
    // TODO: redirect to /api/auth/login (Google OAuth)
    window.location.href = "/api/auth/login";
  }, []);

  const logout = useCallback(() => {
    // TODO: call /api/auth/logout, clear state
    setUser(null);
    window.location.href = "/login";
  }, []);

  return { user, isLoading, login, logout, setUser, setIsLoading };
}
