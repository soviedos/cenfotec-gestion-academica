import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { AuthContext } from "@/features/auth/context/AuthContext";
import { AuthGuard } from "@/features/auth/components/AuthGuard";
import type { AuthContextValue } from "@/features/auth/context/AuthContext";
import type { AuthStatus } from "@/features/auth/types/auth";

const mockReplace = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: mockReplace }),
}));

function renderGuard(status: AuthStatus) {
  const value: AuthContextValue = {
    user: null,
    status,
    isAuthenticated: status === "authenticated",
    login: vi.fn(),
    logout: vi.fn(),
  };

  return render(
    <AuthContext.Provider value={value}>
      <AuthGuard>
        <p>Protected content</p>
      </AuthGuard>
    </AuthContext.Provider>,
  );
}

describe("AuthGuard", () => {
  beforeEach(() => {
    mockReplace.mockClear();
  });

  it("shows loading indicator while checking auth", () => {
    renderGuard("loading");
    expect(screen.getByText("Cargando…")).toBeInTheDocument();
    expect(screen.queryByText("Protected content")).not.toBeInTheDocument();
  });

  it("renders children when authenticated", () => {
    renderGuard("authenticated");
    expect(screen.getByText("Protected content")).toBeInTheDocument();
  });

  it("redirects to /login when unauthenticated", () => {
    renderGuard("unauthenticated");
    expect(mockReplace).toHaveBeenCalledWith("/login");
    expect(screen.queryByText("Protected content")).not.toBeInTheDocument();
  });
});
