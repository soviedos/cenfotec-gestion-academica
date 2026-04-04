import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  DashboardEmpty,
  DashboardError,
  DashboardSkeleton,
} from "@/components/dashboard/dashboard-states";

describe("DashboardEmpty", () => {
  it("renders the empty state message", () => {
    render(<DashboardEmpty />);
    expect(
      screen.getByText("Sin datos de evaluaciones"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Suba archivos PDF/),
    ).toBeInTheDocument();
  });
});

describe("DashboardError", () => {
  it("renders error message", () => {
    render(<DashboardError message="Conexión rechazada" onRetry={() => {}} />);
    expect(screen.getByText("Conexión rechazada")).toBeInTheDocument();
  });

  it("renders retry button", () => {
    render(<DashboardError message="Error" onRetry={() => {}} />);
    expect(screen.getByText("Reintentar")).toBeInTheDocument();
  });
});

describe("DashboardSkeleton", () => {
  it("renders skeleton placeholders", () => {
    const { container } = render(<DashboardSkeleton />);
    const pulseElements = container.querySelectorAll(".animate-pulse");
    // 4 KPI + 2 chart row 1 + 2 chart row 2 = 8
    expect(pulseElements.length).toBe(8);
  });
});
