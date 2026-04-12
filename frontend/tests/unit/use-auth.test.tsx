import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import type { ReactNode } from "react";
import { AuthProvider } from "@/features/auth/context/AuthContext";
import { useAuth } from "@/features/auth/hooks/useAuth";
import type { User } from "@/features/auth/types/auth";
import { Role } from "@/features/auth/types/auth";

// Mock the authApi module
vi.mock("@/features/auth/lib/authApi", () => ({
  getToken: vi.fn(() => null),
  setToken: vi.fn(),
  clearToken: vi.fn(),
  fetchCurrentUser: vi.fn(),
}));

// Import after mock
import * as authApi from "@/features/auth/lib/authApi";

const wrapper = ({ children }: { children: ReactNode }) => (
  <AuthProvider>{children}</AuthProvider>
);

const mockUser: User = {
  id: "u1",
  email: "admin@cenfotec.ac.cr",
  nombre: "Admin",
  avatar_url: null,
  role: Role.ADMIN,
  activo: true,
  modulos: [
    { modulo: "evaluacion_docente", permisos: ["read", "write", "admin"] },
  ],
};

describe("useAuth", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("throws when used outside AuthProvider", () => {
    // Suppress console.error for this test
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    expect(() => renderHook(() => useAuth())).toThrow(
      "useAuth debe usarse dentro de <AuthProvider>",
    );
    spy.mockRestore();
  });

  it("starts in loading state and resolves to unauthenticated", async () => {
    vi.mocked(authApi.fetchCurrentUser).mockResolvedValue(null);

    const { result } = renderHook(() => useAuth(), { wrapper });

    // After the effect settles
    await vi.waitFor(() => {
      expect(result.current.status).toBe("unauthenticated");
    });
    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  it("resolves to authenticated when fetchCurrentUser returns user", async () => {
    vi.mocked(authApi.fetchCurrentUser).mockResolvedValue(mockUser);

    const { result } = renderHook(() => useAuth(), { wrapper });

    await vi.waitFor(() => {
      expect(result.current.status).toBe("authenticated");
    });
    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isAuthenticated).toBe(true);
  });

  it("login stores token and loads user", async () => {
    vi.mocked(authApi.fetchCurrentUser)
      .mockResolvedValueOnce(null) // initial check
      .mockResolvedValueOnce(mockUser); // after login

    const { result } = renderHook(() => useAuth(), { wrapper });

    await vi.waitFor(() => {
      expect(result.current.status).toBe("unauthenticated");
    });

    await act(async () => {
      await result.current.login("new-token");
    });

    expect(authApi.setToken).toHaveBeenCalledWith("new-token");
    expect(result.current.status).toBe("authenticated");
    expect(result.current.user).toEqual(mockUser);
  });

  it("logout clears token and resets state", async () => {
    vi.mocked(authApi.fetchCurrentUser).mockResolvedValue(mockUser);

    const { result } = renderHook(() => useAuth(), { wrapper });

    await vi.waitFor(() => {
      expect(result.current.status).toBe("authenticated");
    });

    act(() => {
      result.current.logout();
    });

    expect(authApi.clearToken).toHaveBeenCalled();
    expect(result.current.user).toBeNull();
    expect(result.current.status).toBe("unauthenticated");
  });
});
