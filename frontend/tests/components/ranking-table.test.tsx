import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { RankingTable } from "@/components/dashboard/ranking-table";
import type { RankingDocente } from "@/types";

const mockData: RankingDocente[] = [
  { posicion: 1, docente_nombre: "Prof. López", promedio: 95.2, evaluaciones_count: 3 },
  { posicion: 2, docente_nombre: "Prof. García", promedio: 88.5, evaluaciones_count: 5 },
  { posicion: 3, docente_nombre: "Prof. Rodríguez", promedio: 82.1, evaluaciones_count: 2 },
  { posicion: 4, docente_nombre: "Prof. Martínez", promedio: 78.0, evaluaciones_count: 1 },
];

describe("RankingTable", () => {
  it("renders all ranked teachers", () => {
    render(<RankingTable data={mockData} />);
    expect(screen.getByText("Prof. López")).toBeInTheDocument();
    expect(screen.getByText("Prof. García")).toBeInTheDocument();
    expect(screen.getByText("Prof. Rodríguez")).toBeInTheDocument();
    expect(screen.getByText("Prof. Martínez")).toBeInTheDocument();
  });

  it("shows position numbers", () => {
    render(<RankingTable data={mockData} />);
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
  });

  it("shows promedio percentages", () => {
    render(<RankingTable data={mockData} />);
    expect(screen.getByText("95.2%")).toBeInTheDocument();
    expect(screen.getByText("88.5%")).toBeInTheDocument();
  });

  it("pluralizes 'evaluaciones' correctly", () => {
    render(<RankingTable data={mockData} />);
    expect(screen.getByText("3 evaluaciones")).toBeInTheDocument();
    expect(screen.getByText("1 evaluación")).toBeInTheDocument();
  });

  it("renders empty state when no data", () => {
    render(<RankingTable data={[]} />);
    expect(
      screen.getByText("No hay datos de ranking disponibles."),
    ).toBeInTheDocument();
  });

  it("renders card title with trophy icon", () => {
    render(<RankingTable data={mockData} />);
    expect(screen.getByText("Ranking docentes")).toBeInTheDocument();
  });
});
