import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { KpiCard } from "@/components/dashboard/kpi-card";
import { TrendingUp } from "lucide-react";

describe("KpiCard", () => {
  it("renders label and value", () => {
    render(
      <KpiCard label="Promedio global" value="87.5%" icon={TrendingUp} />,
    );
    expect(screen.getByText("Promedio global")).toBeInTheDocument();
    expect(screen.getByText("87.5%")).toBeInTheDocument();
  });

  it("renders description when provided", () => {
    render(
      <KpiCard
        label="Evaluaciones"
        value={42}
        icon={TrendingUp}
        description="Total procesadas"
      />,
    );
    expect(screen.getByText("Total procesadas")).toBeInTheDocument();
  });

  it("renders positive trend with green color", () => {
    render(
      <KpiCard
        label="Promedio"
        value="90%"
        icon={TrendingUp}
        trend={{ value: 5.2, label: "vs período anterior" }}
      />,
    );
    const trendEl = screen.getByText("+5.2%");
    expect(trendEl).toBeInTheDocument();
    expect(trendEl.className).toContain("text-emerald-600");
  });

  it("renders negative trend with red color", () => {
    render(
      <KpiCard
        label="Promedio"
        value="80%"
        icon={TrendingUp}
        trend={{ value: -3.1, label: "vs período anterior" }}
      />,
    );
    const trendEl = screen.getByText("-3.1%");
    expect(trendEl).toBeInTheDocument();
    expect(trendEl.className).toContain("text-red-500");
  });

  it("renders numeric value correctly", () => {
    render(<KpiCard label="Docentes" value={15} icon={TrendingUp} />);
    expect(screen.getByText("15")).toBeInTheDocument();
  });
});
