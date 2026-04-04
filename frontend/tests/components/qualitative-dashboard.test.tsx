import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QualitativeDashboard } from "@/components/sentimiento/qualitative-dashboard";
import type {
  ComentarioAnalisis,
  ResumenCualitativo,
  SentimientoDistribucion,
  TemaDistribucion,
} from "@/types";

// Mock recharts to avoid ResizeObserver issues in jsdom
vi.mock("recharts", () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  PieChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="pie-chart">{children}</div>
  ),
  Pie: () => null,
  Cell: () => null,
  Legend: () => null,
  BarChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="bar-chart">{children}</div>
  ),
  Bar: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
}));

// ── Mock data ──────────────────────────────────────────────────────────

const mockResumen: ResumenCualitativo = {
  total_comentarios: 25,
  por_tipo: [
    { tipo: "fortaleza", count: 15 },
    { tipo: "mejora", count: 8 },
    { tipo: "observacion", count: 2 },
  ],
  por_sentimiento: [
    { sentimiento: "positivo", count: 14, porcentaje: 56 },
    { sentimiento: "neutro", count: 5, porcentaje: 20 },
    { sentimiento: "negativo", count: 4, porcentaje: 16 },
    { sentimiento: "mixto", count: 2, porcentaje: 8 },
  ],
  temas_top: [
    { tema: "metodologia", count: 8, porcentaje: 32 },
    { tema: "comunicacion", count: 6, porcentaje: 24 },
  ],
  sentimiento_promedio: 0.72,
};

const mockComentarios: ComentarioAnalisis[] = [
  {
    id: "c1",
    evaluacion_id: "e1",
    fuente: "Estudiante",
    asignatura: "Programación I",
    tipo: "fortaleza",
    texto: "Excelente profesor, muy claro en sus explicaciones.",
    tema: "comunicacion",
    tema_confianza: "regla",
    sentimiento: "positivo",
    sent_score: 0.85,
    procesado_ia: false,
  },
  {
    id: "c2",
    evaluacion_id: "e2",
    fuente: "Director",
    asignatura: "Base de datos",
    tipo: "mejora",
    texto: "Debería mejorar la puntualidad en la entrega de notas.",
    tema: "puntualidad",
    tema_confianza: "regla",
    sentimiento: "negativo",
    sent_score: 0.3,
    procesado_ia: false,
  },
];

const mockTemas: TemaDistribucion[] = [
  { tema: "metodologia", count: 8, porcentaje: 32 },
  { tema: "comunicacion", count: 6, porcentaje: 24 },
  { tema: "puntualidad", count: 4, porcentaje: 16 },
];

const mockSentimientos: SentimientoDistribucion[] = [
  { sentimiento: "positivo", count: 14, porcentaje: 56 },
  { sentimiento: "neutro", count: 5, porcentaje: 20 },
  { sentimiento: "negativo", count: 4, porcentaje: 16 },
  { sentimiento: "mixto", count: 2, porcentaje: 8 },
];

// ── Mock API ───────────────────────────────────────────────────────────

vi.mock("@/lib/api/qualitative", () => ({
  fetchFiltrosCualitativos: vi.fn(),
  fetchResumenCualitativo: vi.fn(),
  fetchComentarios: vi.fn(),
  fetchDistribucionTemas: vi.fn(),
  fetchDistribucionSentimiento: vi.fn(),
  fetchNubePalabras: vi.fn(),
}));

import {
  fetchFiltrosCualitativos,
  fetchResumenCualitativo,
  fetchComentarios,
  fetchDistribucionTemas,
  fetchDistribucionSentimiento,
} from "@/lib/api/qualitative";

const mockedFetchFiltros = vi.mocked(fetchFiltrosCualitativos);
const mockedFetchResumen = vi.mocked(fetchResumenCualitativo);
const mockedFetchComentarios = vi.mocked(fetchComentarios);
const mockedFetchTemas = vi.mocked(fetchDistribucionTemas);
const mockedFetchSentimientos = vi.mocked(fetchDistribucionSentimiento);

function setupMocks(overrides?: { empty?: boolean }) {
  mockedFetchFiltros.mockResolvedValue({
    periodos: ["2025-1", "2024-3"],
    docentes: ["Prof. López", "Prof. García"],
    asignaturas: ["Programación I", "Base de datos"],
    escuelas: ["ESC ING DEL SOFTWARE", "ESC FUNDAMENTOS"],
  });

  if (overrides?.empty) {
    mockedFetchResumen.mockResolvedValue({
      total_comentarios: 0,
      por_tipo: [],
      por_sentimiento: [],
      temas_top: [],
      sentimiento_promedio: null,
    });
    mockedFetchComentarios.mockResolvedValue([]);
    mockedFetchTemas.mockResolvedValue([]);
    mockedFetchSentimientos.mockResolvedValue([]);
  } else {
    mockedFetchResumen.mockResolvedValue(mockResumen);
    mockedFetchComentarios.mockResolvedValue(mockComentarios);
    mockedFetchTemas.mockResolvedValue(mockTemas);
    mockedFetchSentimientos.mockResolvedValue(mockSentimientos);
  }
}

beforeEach(() => {
  vi.clearAllMocks();
  // Default filtros mock for all tests
  mockedFetchFiltros.mockResolvedValue({
    periodos: [],
    docentes: [],
    asignaturas: [],
    escuelas: [],
  });
});

// ── Tests ──────────────────────────────────────────────────────────────

describe("QualitativeDashboard", () => {
  it("shows skeleton while loading", () => {
    mockedFetchResumen.mockReturnValue(new Promise(() => {}));
    mockedFetchComentarios.mockReturnValue(new Promise(() => {}));
    mockedFetchTemas.mockReturnValue(new Promise(() => {}));
    mockedFetchSentimientos.mockReturnValue(new Promise(() => {}));

    const { container } = render(<QualitativeDashboard />);
    const pulseElements = container.querySelectorAll(".animate-pulse");
    expect(pulseElements.length).toBeGreaterThan(0);
  });

  it("renders KPI cards with data", async () => {
    setupMocks();
    render(<QualitativeDashboard />);
    await waitFor(() => {
      expect(screen.getByText("25")).toBeInTheDocument();
    });
    expect(screen.getByText("14")).toBeInTheDocument(); // positivos
    expect(screen.getByText("4")).toBeInTheDocument(); // negativos
    expect(screen.getByText("72%")).toBeInTheDocument(); // score promedio
  });

  it("renders chart containers", async () => {
    setupMocks();
    render(<QualitativeDashboard />);
    await waitFor(() => {
      expect(
        screen.getByText("Distribución por sentimiento"),
      ).toBeInTheDocument();
    });
    expect(screen.getByText("Temas recurrentes")).toBeInTheDocument();
  });

  it("renders comment table", async () => {
    setupMocks();
    render(<QualitativeDashboard />);
    await waitFor(() => {
      expect(screen.getByText("Comentarios clasificados")).toBeInTheDocument();
    });
    expect(
      screen.getByText(/Excelente profesor, muy claro en sus explicaciones/),
    ).toBeInTheDocument();
  });

  it("shows empty state when no data", async () => {
    setupMocks({ empty: true });
    render(<QualitativeDashboard />);
    await waitFor(() => {
      expect(
        screen.getByText("Sin comentarios analizados"),
      ).toBeInTheDocument();
    });
  });

  it("shows error state on API failure", async () => {
    mockedFetchResumen.mockRejectedValue(new Error("Network error"));
    mockedFetchComentarios.mockRejectedValue(new Error("Network error"));
    mockedFetchTemas.mockRejectedValue(new Error("Network error"));
    mockedFetchSentimientos.mockRejectedValue(new Error("Network error"));

    render(<QualitativeDashboard />);
    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });
    expect(screen.getByText("Reintentar")).toBeInTheDocument();
  });

  it("renders filter buttons", async () => {
    setupMocks();
    render(<QualitativeDashboard />);
    await waitFor(() => {
      expect(screen.getByText("Tipo:")).toBeInTheDocument();
    });
    expect(screen.getByText("Sentimiento:")).toBeInTheDocument();
    expect(screen.getByText("Tema:")).toBeInTheDocument();
    // Filter buttons are present (some may also appear in table badges)
    expect(screen.getAllByText("Fortaleza").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Positivo").length).toBeGreaterThanOrEqual(1);
  });

  it("applies tipo filter on click", async () => {
    setupMocks();
    const user = userEvent.setup();
    render(<QualitativeDashboard />);

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Fortaleza" }),
      ).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Fortaleza" }));

    // Should re-fetch with tipo filter
    await waitFor(() => {
      expect(mockedFetchComentarios).toHaveBeenCalledWith(
        expect.objectContaining({ tipo: "fortaleza" }),
      );
    });
  });

  it("clears all filters", async () => {
    setupMocks();
    const user = userEvent.setup();
    render(<QualitativeDashboard />);

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Fortaleza" }),
      ).toBeInTheDocument();
    });

    // Apply a filter first
    await user.click(screen.getByRole("button", { name: "Fortaleza" }));

    await waitFor(() => {
      expect(screen.getByText("Limpiar filtros")).toBeInTheDocument();
    });

    await user.click(screen.getByText("Limpiar filtros"));

    // After clearing, the filter should be gone—fetches reset
    await waitFor(() => {
      const lastCall = mockedFetchComentarios.mock.calls.at(-1);
      expect(lastCall?.[0]).toEqual(
        expect.objectContaining({ tipo: undefined }),
      );
    });
  });
});
