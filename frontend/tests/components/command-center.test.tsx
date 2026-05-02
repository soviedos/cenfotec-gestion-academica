import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CommandCenter } from "@/features/evaluacion-docente/components/dashboard/command-center";
import type {
  AlertaResponse,
  AlertaSummary,
  DashboardSummary,
  PaginatedResponse,
} from "@/features/evaluacion-docente/types";

// ── Mock recharts ───────────────────────────────────────────────

vi.mock("recharts", () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  AreaChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="area-chart">{children}</div>
  ),
  Area: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
}));

// ── Mock API ────────────────────────────────────────────────────

vi.mock("@/features/evaluacion-docente/lib/api/dashboard", () => ({
  fetchDashboardSummary: vi.fn(),
}));

vi.mock("@/features/evaluacion-docente/lib/api/alertas", () => ({
  fetchAlertSummary: vi.fn(),
  fetchAlerts: vi.fn(),
}));

vi.mock("@/features/evaluacion-docente/lib/api/analytics", () => ({
  fetchEscuelas: vi.fn().mockResolvedValue([]),
}));

import { fetchDashboardSummary } from "@/features/evaluacion-docente/lib/api/dashboard";
import {
  fetchAlertSummary,
  fetchAlerts,
} from "@/features/evaluacion-docente/lib/api/alertas";

const mockedFetchDashboard = vi.mocked(fetchDashboardSummary);
const mockedFetchAlertSummary = vi.mocked(fetchAlertSummary);
const mockedFetchAlerts = vi.mocked(fetchAlerts);

// ── Fixtures ────────────────────────────────────────────────────

const MOCK_DASHBOARD: DashboardSummary = {
  kpis: {
    documentos_procesados: 25,
    docentes_evaluados: 12,
    promedio_general: 82.5,
    alertas_criticas: 3,
  },
  alertas: [],
  tendencia: [
    {
      periodo: "C1 2025",
      promedio: 80,
      evaluaciones_count: 10,
      año: 2025,
      periodo_orden: 1,
    },
    {
      periodo: "C2 2025",
      promedio: 85,
      evaluaciones_count: 15,
      año: 2025,
      periodo_orden: 2,
    },
  ],
  top_docentes: [
    {
      posicion: 1,
      docente_nombre: "Prof. López",
      promedio: 95,
      evaluaciones_count: 4,
    },
    {
      posicion: 2,
      docente_nombre: "Prof. García",
      promedio: 92,
      evaluaciones_count: 3,
    },
  ],
  bottom_docentes: [
    {
      posicion: 1,
      docente_nombre: "Prof. Ruiz",
      promedio: 55,
      evaluaciones_count: 2,
    },
  ],
  insights: [
    {
      icono: "info",
      texto: "El promedio general subió 5 puntos vs periodo anterior.",
    },
  ],
  actividad_reciente: [
    {
      documento_nombre: "evaluaciones_C2_2025.pdf",
      estado: "procesado",
      evaluaciones_extraidas: 10,
      fecha: "2025-06-15T10:30:00Z",
    },
  ],
};

const MOCK_ALERT_SUMMARY: AlertaSummary = {
  total_activas: 7,
  por_severidad: { alta: 3, media: 2, baja: 2 },
  por_tipo: { BAJO_DESEMPEÑO: 4, CAIDA: 2, SENTIMIENTO: 1 },
  por_modalidad: { CUATRIMESTRAL: 5, MENSUAL: 2 },
  docentes_afectados: 5,
};

const MOCK_CRITICAL_ALERTS: AlertaResponse[] = [
  {
    id: "alert-1",
    evaluacion_id: "eval-1",
    docente_nombre: "Prof. Ruiz",
    curso: "Programación I",
    periodo: "C2 2025",
    modalidad: "CUATRIMESTRAL",
    tipo_alerta: "BAJO_DESEMPEÑO",
    metrica_afectada: "puntaje_general",
    valor_actual: 45.2,
    valor_anterior: null,
    descripcion: "Puntaje 45.2% está por debajo del umbral de 60%",
    severidad: "alta",
    estado: "activa",
    created_at: "2025-06-15T10:00:00Z",
    updated_at: "2025-06-15T10:00:00Z",
  },
  {
    id: "alert-2",
    evaluacion_id: "eval-2",
    docente_nombre: "Prof. Méndez",
    curso: "Base de datos II",
    periodo: "C2 2025",
    modalidad: "CUATRIMESTRAL",
    tipo_alerta: "CAIDA",
    metrica_afectada: "puntaje_general",
    valor_actual: 58.0,
    valor_anterior: 78.5,
    descripcion: "Caída de 20.5 puntos vs periodo anterior",
    severidad: "alta",
    estado: "activa",
    created_at: "2025-06-15T10:00:00Z",
    updated_at: "2025-06-15T10:00:00Z",
  },
];

const MOCK_ALERTS_PAGE: PaginatedResponse<AlertaResponse> = {
  items: MOCK_CRITICAL_ALERTS,
  total: 2,
  page: 1,
  page_size: 10,
  total_pages: 1,
};

const EMPTY_DASHBOARD: DashboardSummary = {
  kpis: {
    documentos_procesados: 0,
    docentes_evaluados: 0,
    promedio_general: 0,
    alertas_criticas: 0,
  },
  alertas: [],
  tendencia: [],
  top_docentes: [],
  bottom_docentes: [],
  insights: [],
  actividad_reciente: [],
};

// ── Helpers ─────────────────────────────────────────────────────

function setupMocks(opts?: { empty?: boolean; error?: boolean }) {
  if (opts?.error) {
    mockedFetchDashboard.mockRejectedValue(new Error("Conexión rechazada"));
    mockedFetchAlertSummary.mockRejectedValue(new Error("Conexión rechazada"));
    mockedFetchAlerts.mockRejectedValue(new Error("Conexión rechazada"));
    return;
  }

  if (opts?.empty) {
    mockedFetchDashboard.mockResolvedValue(EMPTY_DASHBOARD);
    mockedFetchAlertSummary.mockResolvedValue({
      total_activas: 0,
      por_severidad: {},
      por_tipo: {},
      por_modalidad: {},
      docentes_afectados: 0,
    });
    mockedFetchAlerts.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 10,
      total_pages: 0,
    });
    return;
  }

  mockedFetchDashboard.mockResolvedValue(MOCK_DASHBOARD);
  mockedFetchAlertSummary.mockResolvedValue(MOCK_ALERT_SUMMARY);
  mockedFetchAlerts.mockResolvedValue(MOCK_ALERTS_PAGE);
}

beforeEach(() => {
  vi.clearAllMocks();
});

// ── Tests ───────────────────────────────────────────────────────

describe("CommandCenter", () => {
  it("shows skeleton while loading", () => {
    mockedFetchDashboard.mockReturnValue(new Promise(() => {}));
    mockedFetchAlertSummary.mockReturnValue(new Promise(() => {}));
    mockedFetchAlerts.mockReturnValue(new Promise(() => {}));

    const { container } = render(<CommandCenter />);
    const pulseElements = container.querySelectorAll(".animate-pulse");
    expect(pulseElements.length).toBeGreaterThan(0);
  });

  it("shows error state with retry button", async () => {
    setupMocks({ error: true });
    render(<CommandCenter />);

    await waitFor(() => {
      expect(screen.getByText("Conexión rechazada")).toBeInTheDocument();
    });
    expect(screen.getByText("Reintentar")).toBeInTheDocument();
  });

  it("shows empty state when no evaluations exist", async () => {
    setupMocks({ empty: true });
    render(<CommandCenter />);

    await waitFor(() => {
      expect(screen.getByText("Sin datos de evaluaciones")).toBeInTheDocument();
    });
  });

  it("renders KPI cards with data", async () => {
    setupMocks();
    render(<CommandCenter />);

    await waitFor(() => {
      expect(screen.getByText("25")).toBeInTheDocument();
    });
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("82.5%")).toBeInTheDocument();
  });

  it("renders real alert count from alert summary", async () => {
    setupMocks();
    const user = userEvent.setup();
    render(<CommandCenter />);

    // Select a modalidad to trigger alert fetch
    await waitFor(() => {
      expect(
        screen.getByRole("tab", { name: "Cuatrimestral" }),
      ).toBeInTheDocument();
    });
    await user.click(screen.getByRole("tab", { name: "Cuatrimestral" }));

    await waitFor(() => {
      // Alert summary total_activas = 7, overrides kpis.alertas_criticas = 3
      expect(screen.getByText("7")).toBeInTheDocument();
    });
  });

  it("renders alert summary with severity breakdown", async () => {
    setupMocks();
    const user = userEvent.setup();
    render(<CommandCenter />);

    await waitFor(() => {
      expect(
        screen.getByRole("tab", { name: "Cuatrimestral" }),
      ).toBeInTheDocument();
    });
    await user.click(screen.getByRole("tab", { name: "Cuatrimestral" }));

    await waitFor(() => {
      expect(screen.getByText("Resumen de alertas")).toBeInTheDocument();
    });
    // alta=3, media=2, baja=2 rendered in severity boxes
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getAllByText("2").length).toBeGreaterThanOrEqual(2);
  });

  it("renders critical alerts panel with real alert data", async () => {
    setupMocks();
    const user = userEvent.setup();
    render(<CommandCenter />);

    await waitFor(() => {
      expect(
        screen.getByRole("tab", { name: "Cuatrimestral" }),
      ).toBeInTheDocument();
    });
    await user.click(screen.getByRole("tab", { name: "Cuatrimestral" }));

    await waitFor(() => {
      expect(screen.getByText(/Alertas \(2\)/)).toBeInTheDocument();
    });
    expect(screen.getByText("Prof. Méndez")).toBeInTheDocument();
    expect(screen.getByText("45.2%")).toBeInTheDocument();
    expect(screen.getByText("58.0%")).toBeInTheDocument();
    // Prof. Ruiz appears in both alerts and bottom docentes
    expect(screen.getAllByText("Prof. Ruiz").length).toBeGreaterThanOrEqual(1);
  });

  it("shows alert tipo labels correctly", async () => {
    setupMocks();
    const user = userEvent.setup();
    render(<CommandCenter />);

    await waitFor(() => {
      expect(
        screen.getByRole("tab", { name: "Cuatrimestral" }),
      ).toBeInTheDocument();
    });
    await user.click(screen.getByRole("tab", { name: "Cuatrimestral" }));

    await waitFor(() => {
      expect(screen.getByText("Bajo desempeño")).toBeInTheDocument();
    });
    expect(screen.getByText("Caída")).toBeInTheDocument();
  });

  it("shows valor_anterior when present", async () => {
    setupMocks();
    const user = userEvent.setup();
    render(<CommandCenter />);

    await waitFor(() => {
      expect(
        screen.getByRole("tab", { name: "Cuatrimestral" }),
      ).toBeInTheDocument();
    });
    await user.click(screen.getByRole("tab", { name: "Cuatrimestral" }));

    await waitFor(() => {
      expect(screen.getByText("ant: 78.5%")).toBeInTheDocument();
    });
  });

  it("renders modalidad selector with all options", async () => {
    setupMocks();
    render(<CommandCenter />);

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: "Todas" })).toBeInTheDocument();
    });
    expect(
      screen.getByRole("tab", { name: "Cuatrimestral" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Mensual" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "B2B" })).toBeInTheDocument();
  });

  it("filters alerts when selecting a modalidad", async () => {
    setupMocks();
    const user = userEvent.setup();
    render(<CommandCenter />);

    await waitFor(() => {
      expect(
        screen.getByRole("tab", { name: "Cuatrimestral" }),
      ).toBeInTheDocument();
    });

    await user.click(screen.getByRole("tab", { name: "Cuatrimestral" }));

    await waitFor(() => {
      expect(mockedFetchAlerts).toHaveBeenCalledWith(
        expect.objectContaining({ modalidad: "CUATRIMESTRAL" }),
        expect.any(Object),
      );
    });
  });

  it("renders top docentes", async () => {
    setupMocks();
    render(<CommandCenter />);

    await waitFor(() => {
      expect(screen.getByText("Top docentes")).toBeInTheDocument();
    });
    expect(screen.getByText("Prof. López")).toBeInTheDocument();
    expect(screen.getByText("Prof. García")).toBeInTheDocument();
  });

  it("renders bottom docentes", async () => {
    setupMocks();
    const user = userEvent.setup();
    render(<CommandCenter />);

    await waitFor(() => {
      expect(
        screen.getByRole("tab", { name: "Cuatrimestral" }),
      ).toBeInTheDocument();
    });
    await user.click(screen.getByRole("tab", { name: "Cuatrimestral" }));

    await waitFor(() => {
      expect(
        screen.getByText("Docentes con menor puntaje"),
      ).toBeInTheDocument();
    });
    // Prof. Ruiz appears in both alerts panel and bottom docentes
    expect(screen.getAllByText("Prof. Ruiz").length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText("55%")).toBeInTheDocument();
  });

  it("renders insights section", async () => {
    setupMocks();
    render(<CommandCenter />);

    await waitFor(() => {
      expect(screen.getByText("Insights automáticos")).toBeInTheDocument();
    });
    expect(
      screen.getByText(
        "El promedio general subió 5 puntos vs periodo anterior.",
      ),
    ).toBeInTheDocument();
  });

  it("renders recent activity", async () => {
    setupMocks();
    render(<CommandCenter />);

    await waitFor(() => {
      expect(screen.getByText("Actividad reciente")).toBeInTheDocument();
    });
    expect(screen.getByText("evaluaciones_C2_2025.pdf")).toBeInTheDocument();
    expect(screen.getByText("Procesado")).toBeInTheDocument();
  });

  it("renders trend chart area", async () => {
    setupMocks();
    render(<CommandCenter />);

    await waitFor(() => {
      expect(screen.getByText("Tendencia por período")).toBeInTheDocument();
    });
    expect(screen.getByTestId("area-chart")).toBeInTheDocument();
  });

  it("renders quick actions links", async () => {
    setupMocks();
    render(<CommandCenter />);

    await waitFor(() => {
      expect(screen.getByText("Acciones rápidas")).toBeInTheDocument();
    });
    expect(screen.getByText("Subir PDF")).toBeInTheDocument();
    expect(screen.getByText("Biblioteca")).toBeInTheDocument();
    expect(screen.getByText("Estadísticas")).toBeInTheDocument();
    expect(screen.getByText("Consultas IA")).toBeInTheDocument();
  });

  it("shows empty alert state when no critical alerts", async () => {
    mockedFetchDashboard.mockResolvedValue(MOCK_DASHBOARD);
    mockedFetchAlertSummary.mockResolvedValue({
      total_activas: 0,
      por_severidad: {},
      por_tipo: {},
      por_modalidad: {},
      docentes_afectados: 0,
    });
    mockedFetchAlerts.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 10,
      total_pages: 0,
    });
    const user = userEvent.setup();
    render(<CommandCenter />);

    // Select a modalidad so alert APIs are actually called
    await waitFor(() => {
      expect(
        screen.getByRole("tab", { name: "Cuatrimestral" }),
      ).toBeInTheDocument();
    });
    await user.click(screen.getByRole("tab", { name: "Cuatrimestral" }));

    await waitFor(() => {
      expect(screen.getByText(/No hay alertas/)).toBeInTheDocument();
    });
  });

  it("renders tipo distribution badges in alert summary", async () => {
    setupMocks();
    const user = userEvent.setup();
    render(<CommandCenter />);

    await waitFor(() => {
      expect(
        screen.getByRole("tab", { name: "Cuatrimestral" }),
      ).toBeInTheDocument();
    });
    await user.click(screen.getByRole("tab", { name: "Cuatrimestral" }));

    await waitFor(() => {
      expect(screen.getByText(/Bajo desempeño: 4/)).toBeInTheDocument();
    });
    expect(screen.getByText(/Caída: 2/)).toBeInTheDocument();
    expect(screen.getByText(/Sentimiento: 1/)).toBeInTheDocument();
  });

  it("all tabs are accessible with proper aria attributes", async () => {
    setupMocks();
    render(<CommandCenter />);

    await waitFor(() => {
      const tablist = screen.getByRole("tablist", {
        name: "Filtro de modalidad",
      });
      expect(tablist).toBeInTheDocument();
    });

    const tabs = screen.getAllByRole("tab");
    expect(tabs).toHaveLength(4); // Todas + 3 modalidades

    // "Todas" selected by default
    expect(screen.getByRole("tab", { name: "Todas" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
  });
});
