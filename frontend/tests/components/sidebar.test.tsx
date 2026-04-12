import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Sidebar } from "@/components/layout/sidebar";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  usePathname: () => "/evaluacion-docente/inicio",
}));

// Mock useModuleAccess — admin sees all modules
vi.mock("@/features/auth/hooks/useModuleAccess", () => ({
  useModuleAccess: () => ({
    hasModule: () => true,
    hasPermission: () => true,
    accessibleModules: [],
  }),
}));

describe("Sidebar", () => {
  const defaultProps = { collapsed: false, onToggle: vi.fn() };

  it("renders the brand logo", () => {
    render(<Sidebar {...defaultProps} />);
    expect(screen.getByAltText("Universidad CENFOTEC")).toBeInTheDocument();
  });

  it("renders all 9 navigation items", () => {
    render(<Sidebar {...defaultProps} />);

    const expectedLabels = [
      "Dashboard",
      "Centro de Mando",
      "Carga de PDFs",
      "Biblioteca",
      "Docentes",
      "Estadístico",
      "Sentimiento",
      "Consultas IA",
      "Reportes",
    ];

    for (const label of expectedLabels) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
  });

  it("renders group titles", () => {
    render(<Sidebar {...defaultProps} />);
    expect(screen.getByText("Plataforma")).toBeInTheDocument();
    expect(screen.getByText("Evaluación Docente")).toBeInTheDocument();
  });

  it("highlights the active route", () => {
    render(<Sidebar {...defaultProps} />);
    const activeLink = screen.getByText("Centro de Mando").closest("a");
    expect(activeLink).toHaveAttribute("href", "/evaluacion-docente/inicio");
    // Active link should have the accent background class
    expect(activeLink?.className).toContain("bg-sidebar-accent");
  });

  it("hides labels when collapsed", () => {
    render(<Sidebar {...{ ...defaultProps, collapsed: true }} />);
    expect(
      screen.queryByAltText("Universidad CENFOTEC"),
    ).not.toBeInTheDocument();
    expect(screen.queryByText("Centro de Mando")).not.toBeInTheDocument();
  });

  it("calls onToggle when collapse button is clicked", async () => {
    const onToggle = vi.fn();
    render(<Sidebar collapsed={false} onToggle={onToggle} />);

    const collapseButton = screen.getByText("Colapsar").closest("button");
    expect(collapseButton).toBeInTheDocument();

    await userEvent.click(collapseButton!);
    expect(onToggle).toHaveBeenCalledTimes(1);
  });
});
