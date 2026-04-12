import { describe, it, expect, vi } from "vitest";
import { renderHook } from "@testing-library/react";
import type { ReactNode } from "react";
import { AuthContext } from "@/features/auth/context/AuthContext";
import { useModuleAccess } from "@/features/auth/hooks/useModuleAccess";
import type { User } from "@/features/auth/types/auth";
import { Role } from "@/features/auth/types/auth";

function makeWrapper(user: User | null) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <AuthContext.Provider
        value={{
          user,
          status: user ? "authenticated" : "unauthenticated",
          isAuthenticated: !!user,
          login: vi.fn(),
          logout: vi.fn(),
        }}
      >
        {children}
      </AuthContext.Provider>
    );
  };
}

const adminUser: User = {
  id: "u1",
  email: "admin@test.com",
  nombre: "Admin",
  avatar_url: null,
  role: Role.ADMIN,
  activo: true,
  modulos: [
    { modulo: "evaluacion_docente", permisos: ["read", "write", "admin"] },
    { modulo: "control_docente", permisos: ["read", "write", "admin"] },
  ],
};

const consultorUser: User = {
  id: "u2",
  email: "consultor@test.com",
  nombre: "Consultor",
  avatar_url: null,
  role: Role.CONSULTOR,
  activo: true,
  modulos: [{ modulo: "evaluacion_docente", permisos: ["read"] }],
};

describe("useModuleAccess", () => {
  it("hasModule returns true for accessible modules", () => {
    const { result } = renderHook(() => useModuleAccess(), {
      wrapper: makeWrapper(adminUser),
    });
    expect(result.current.hasModule("evaluacion_docente")).toBe(true);
    expect(result.current.hasModule("control_docente")).toBe(true);
  });

  it("hasModule returns false for inaccessible modules", () => {
    const { result } = renderHook(() => useModuleAccess(), {
      wrapper: makeWrapper(consultorUser),
    });
    expect(result.current.hasModule("control_docente")).toBe(false);
  });

  it("hasPermission checks specific permissions", () => {
    const { result } = renderHook(() => useModuleAccess(), {
      wrapper: makeWrapper(consultorUser),
    });
    expect(result.current.hasPermission("evaluacion_docente", "read")).toBe(
      true,
    );
    expect(result.current.hasPermission("evaluacion_docente", "write")).toBe(
      false,
    );
  });

  it("accessibleModules returns the user modules list", () => {
    const { result } = renderHook(() => useModuleAccess(), {
      wrapper: makeWrapper(consultorUser),
    });
    expect(result.current.accessibleModules).toEqual([
      { modulo: "evaluacion_docente", permisos: ["read"] },
    ]);
  });

  it("returns empty state when no user", () => {
    const { result } = renderHook(() => useModuleAccess(), {
      wrapper: makeWrapper(null),
    });
    expect(result.current.hasModule("evaluacion_docente")).toBe(false);
    expect(result.current.accessibleModules).toEqual([]);
  });
});
