import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AnalyticsDashboard } from "@/features/evaluacion-docente/components/dashboard/analytics-dashboard";
import type {
  DimensionPromedio,
  DocentePromedio,
  PeriodoMetrica,
  RankingDocente,
  ResumenGeneral,
} from "@/features/evaluacion-docente/types";

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
  {
    dimension: "Metodología",
    pct_estudiante: 88,
    pct_director: 90,
    pct_autoeval: 85,
    pct_promedio: 87.67,
  },
];

const mockEvolucion: PeriodoMetrica[] = [
  {
    periodo: "C1 2025",
    promedio: 85,
    evaluaciones_count: 5,
    modalidad: "CUATRIMESTRAL",
    año: 2025,
    periodo_orden: 1,
  },
  {
    periodo: "C2 2025",
    promedio: 90,
    evaluaciones_count: 5,
    modalidad: "CUATRIMESTRAL",
    año: 2025,
    periodo_orden: 2,
  },
];

const mockRanking: RankingDocente[] = [
  {
    posicion: 1,
    docente_nombre: "Prof. López",
    promedio: 92,
    evaluaciones_count: 4,
  },
];

vi.mock("@/features/evaluacion-docente/lib/api/analytics", () => ({
  fetchResumen: vi.fn(),
  fetchDocentePromedios: vi.fn(),
  fetchDimensiones: vi.fn(),
  fetchEvolucion: vi.fn(),
  fetchRanking: vi.fn(),
  fetchEscuelas: vi.fn(),
  fetchCursos: vi.fn(),
  fetchPeriodos: vi.fn(),
}));

import {
  fetchResumen,
  fetchDocentePromedios,
  fetchDimensiones,
  fetchEvolucion,
  fetchRanking,
  fetchEscuelas,
  fetchCursos,
  fetchPeriodos,
} from "@/features/evaluacion-docente/lib/api/analytics";

const mockedFetchResumen = vi.mocked(fetchResumen);
const mockedFetchDocentes = vi.mocked(fetchDocentePromedios);
const mockedFetchDimensiones = vi.mocked(fetchDimensiones);
const mockedFetchEvolucion = vi.mocked(fetchEvolucion);
const mockedFetchRanking = vi.mocked(fetchRanking);
const mockedFetchEscuelas = vi.mocked(fetchEscuelas);
const mockedFetchCursos = vi.mocked(fetchCursos);
const mockedFetchPeriodos = vi.mocked(fetchPeriodos);

function setupMocks(overrides?: { empty?: boolean }) {
  mockedFetchEscuelas.mockResolvedValue(["Escuela de Ingeniería"]);
  mockedFetchCursos.mockResolvedValue(["Programación I"]);
  mockedFetchPeriodos.mockResolvedValue([
    {
      periodo: "C1 2025",
      modalidad: "CUATRIMESTRAL",
      año: 2025,
      periodo_orden: 1,
    },
    {
      periodo: "C2 2025",
      modalidad: "CUATRIMESTRAL",
      año: 2025,
      periodo_orden: 2,
    },
  ]);
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
    mockedFetchEscuelas.mockResolvedValue([]);
    mockedFetchCursos.mockResolvedValue([]);
    mockedFetchPeriodos.mockResolvedValue([]);

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
      expect(screen.getByText("Sin datos de evaluaciones")).toBeInTheDocument();
    });
  });

  it("shows error state on API failure", async () => {
    mockedFetchResumen.mockRejectedValue(new Error("Network error"));
    mockedFetchDocentes.mockRejectedValue(new Error("Network error"));
    mockedFetchDimensiones.mockRejectedValue(new Error("Network error"));
    mockedFetchEvolucion.mockRejectedValue(new Error("Network error"));
    mockedFetchRanking.mockRejectedValue(new Error("Network error"));
    mockedFetchEscuelas.mockResolvedValue([]);
    mockedFetchCursos.mockResolvedValue([]);
    mockedFetchPeriodos.mockResolvedValue([]);

    render(<AnalyticsDashboard />);
    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });
    expect(screen.getByText("Reintentar")).toBeInTheDocument();
  });

  it("renders modalidad filter buttons from evolucion data", async () => {
    setupMocks();
    render(<AnalyticsDashboard />);
    await waitFor(() => {
      expect(screen.getByText("Cuatrimestral")).toBeInTheDocument();
    });
  });

  it("clicking a modalidad then period filter refetches with params", async () => {
    setupMocks();
    render(<AnalyticsDashboard />);

    // Wait for initial load (no modalidad selected → all data shown)
    await waitFor(() => {
      expect(screen.getByText("87.5%")).toBeInTheDocument();
    });

    const user = userEvent.setup();

    // Click Cuatrimestral to select it → period buttons appear
    await user.click(screen.getByText("Cuatrimestral"));
    await waitFor(() => {
      expect(screen.getByText("C1 2025")).toBeInTheDocument();
    });

    await user.click(screen.getByText("C1 2025"));

    // After clicking, fetchResumen should have been called with periodo + modalidad
    await waitFor(() => {
      expect(mockedFetchResumen).toHaveBeenCalledWith(
        "C1 2025",
        expect.any(AbortSignal),
        "CUATRIMESTRAL",
        undefined,
        undefined,
      );
    });
  });
});
