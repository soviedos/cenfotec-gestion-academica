"use client";

import {
  createContext,
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import type { AuthStatus, User } from "../types/auth";
import { clearToken, fetchCurrentUser, setToken } from "../lib/authApi";

export interface AuthContextValue {
  user: User | null;
  status: AuthStatus;
  isAuthenticated: boolean;
  login: (token: string) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");
  const initialised = useRef(false);

  const loadUser = useCallback(async () => {
    setStatus("loading");
    const u = await fetchCurrentUser();
    if (u) {
      setUser(u);
      setStatus("authenticated");
    } else {
      setUser(null);
      setStatus("unauthenticated");
    }
  }, []);

  // Check for existing token on mount
  useEffect(() => {
    if (initialised.current) return;
    initialised.current = true;

    let cancelled = false;
    fetchCurrentUser().then((u) => {
      if (cancelled) return;
      if (u) {
        setUser(u);
        setStatus("authenticated");
      } else {
        setStatus("unauthenticated");
      }
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(
    async (token: string) => {
      setToken(token);
      await loadUser();
    },
    [loadUser],
  );

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
    setStatus("unauthenticated");
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        status,
        isAuthenticated: status === "authenticated",
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
