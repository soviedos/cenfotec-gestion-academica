import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AnalyticsDashboard } from "@/components/dashboard/analytics-dashboard";
import type {
  DimensionPromedio,
  DocentePromedio,
  PeriodoMetrica,
  RankingDocente,
  ResumenGeneral,
} from "@/types";

// Mock recharts to avoid ResizeObserver issues in jsdom
vi.mock("recharts", () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  BarChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="bar-chart">{children}</div>
  ),
  Bar: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  RadarChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="radar-chart">{children}</div>
  ),
  Radar: () => null,
  PolarGrid: () => null,
  PolarAngleAxis: () => null,
  PolarRadiusAxis: () => null,
  AreaChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="area-chart">{children}</div>
  ),
  Area: () => null,
}));

const mockResumen: ResumenGeneral = {
  promedio_global: 87.5,
  total_evaluaciones: 10,
  total_docentes: 3,
  total_periodos: 2,
};

const mockDocentes: DocentePromedio[] = [
  { docente_nombre: "Prof. López", promedio: 92, evaluaciones_count: 4 },
  { docente_nombre: "Prof. García", promedio: 85, evaluaciones_count: 6 },
];

const mockDimensiones: DimensionPromedio[] = [
  { dimension: "Metodología", pct_estudiante: 88, pct_director: 90, pct_autoeval: 85, pct_promedio: 87.67 },
];

const mockEvolucion: PeriodoMetrica[] = [
  { periodo: "2025-1", promedio: 85, evaluaciones_count: 5 },
  { periodo: "2025-2", promedio: 90, evaluaciones_count: 5 },
];

const mockRanking: RankingDocente[] = [
  { posicion: 1, docente_nombre: "Prof. López", promedio: 92, evaluaciones_count: 4 },
];

vi.mock("@/lib/api/analytics", () => ({
  fetchResumen: vi.fn(),
  fetchDocentePromedios: vi.fn(),
  fetchDimensiones: vi.fn(),
  fetchEvolucion: vi.fn(),
  fetchRanking: vi.fn(),
}));

import {
  fetchResumen,
  fetchDocentePromedios,
  fetchDimensiones,
  fetchEvolucion,
  fetchRanking,
} from "@/lib/api/analytics";

const mockedFetchResumen = vi.mocked(fetchResumen);
const mockedFetchDocentes = vi.mocked(fetchDocentePromedios);
const mockedFetchDimensiones = vi.mocked(fetchDimensiones);
const mockedFetchEvolucion = vi.mocked(fetchEvolucion);
const mockedFetchRanking = vi.mocked(fetchRanking);

function setupMocks(overrides?: { empty?: boolean }) {
  if (overrides?.empty) {
    mockedFetchResumen.mockResolvedValue({
      promedio_global: 0,
      total_evaluaciones: 0,
      total_docentes: 0,
      total_periodos: 0,
    });
    mockedFetchDocentes.mockResolvedValue([]);
    mockedFetchDimensiones.mockResolvedValue([]);
    mockedFetchEvolucion.mockResolvedValue([]);
    mockedFetchRanking.mockResolvedValue([]);
  } else {
    mockedFetchResumen.mockResolvedValue(mockResumen);
    mockedFetchDocentes.mockResolvedValue(mockDocentes);
    mockedFetchDimensiones.mockResolvedValue(mockDimensiones);
    mockedFetchEvolucion.mockResolvedValue(mockEvolucion);
    mockedFetchRanking.mockResolvedValue(mockRanking);
  }
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("AnalyticsDashboard", () => {
  it("shows skeleton while loading", () => {
    // Never resolve — keeps loading
    mockedFetchResumen.mockReturnValue(new Promise(() => {}));
    mockedFetchDocentes.mockReturnValue(new Promise(() => {}));
    mockedFetchDimensiones.mockReturnValue(new Promise(() => {}));
    mockedFetchEvolucion.mockReturnValue(new Promise(() => {}));
    mockedFetchRanking.mockReturnValue(new Promise(() => {}));

    const { container } = render(<AnalyticsDashboard />);
    const pulseElements = container.querySelectorAll(".animate-pulse");
    expect(pulseElements.length).toBeGreaterThan(0);
  });

  it("renders KPI cards with data", async () => {
    setupMocks();
    render(<AnalyticsDashboard />);
    await waitFor(() => {
      expect(screen.getByText("87.5%")).toBeInTheDocument();
    });
    expect(screen.getByText("10")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("renders chart containers", async () => {
    setupMocks();
    render(<AnalyticsDashboard />);
    await waitFor(() => {
      expect(screen.getByText("Promedio por docente")).toBeInTheDocument();
    });
    expect(screen.getByText("Dimensiones de evaluación")).toBeInTheDocument();
    expect(screen.getByText("Tendencia histórica")).toBeInTheDocument();
    expect(screen.getByText("Ranking docentes")).toBeInTheDocument();
  });

  it("shows empty state when no evaluaciones exist", async () => {
    setupMocks({ empty: true });
    render(<AnalyticsDashboard />);
    await waitFor(() => {
      expect(
        screen.getByText("Sin datos de evaluaciones"),
      ).toBeInTheDocument();
    });
  });

  it("shows error state on API failure", async () => {
    mockedFetchResumen.mockRejectedValue(new Error("Network error"));
    mockedFetchDocentes.mockRejectedValue(new Error("Network error"));
    mockedFetchDimensiones.mockRejectedValue(new Error("Network error"));
    mockedFetchEvolucion.mockRejectedValue(new Error("Network error"));
    mockedFetchRanking.mockRejectedValue(new Error("Network error"));

    render(<AnalyticsDashboard />);
    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });
    expect(screen.getByText("Reintentar")).toBeInTheDocument();
  });

  it("renders period filter buttons from evolucion data", async () => {
    setupMocks();
    render(<AnalyticsDashboard />);
    await waitFor(() => {
      expect(screen.getByText("2025-1")).toBeInTheDocument();
    });
    expect(screen.getByText("2025-2")).toBeInTheDocument();
  });

  it("clicking a period filter refetches with periodo param", async () => {
    setupMocks();
    render(<AnalyticsDashboard />);

    await waitFor(() => {
      expect(screen.getByText("2025-1")).toBeInTheDocument();
    });

    const user = userEvent.setup();
    await user.click(screen.getByText("2025-1"));

    // After clicking, fetchResumen should have been called again with periodo
    await waitFor(() => {
      expect(mockedFetchResumen).toHaveBeenCalledWith("2025-1");
    });
  });
});
