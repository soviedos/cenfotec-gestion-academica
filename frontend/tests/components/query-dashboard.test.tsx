import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryDashboard } from "@/components/consultas-ia/query-dashboard";
import type { QueryResponse } from "@/types";

// ── Mock API ───────────────────────────────────────────────────────────

vi.mock("@/lib/api/query", () => ({
  postQuery: vi.fn(),
}));

import { postQuery } from "@/lib/api/query";

const mockedPostQuery = vi.mocked(postQuery);

const mockQueryResponse: QueryResponse = {
  answer: "El docente tiene un promedio de 4.5.",
  confidence: 0.9,
  evidence: [
    {
      type: "metric",
      label: "Promedio general",
      value: 4.5,
      source: { periodo: "2025-1", docente: "Prof. López" },
    },
    {
      type: "comment",
      texto: "Excelente docente.",
      source: {
        evaluacion_id: "e1",
        docente: "Prof. López",
        periodo: "2025-1",
        asignatura: "Programación",
        fuente: "Estudiante",
      },
      relevance_score: 0.9,
    },
  ],
  metadata: {
    model: "gemini-2.0-flash",
    tokens_used: 250,
    latency_ms: 1000,
    audit_log_id: "audit-1",
  },
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe("QueryDashboard", () => {
  it("renders the input card with title", () => {
    render(<QueryDashboard />);
    expect(screen.getByText("Asistente inteligente")).toBeInTheDocument();
    expect(screen.getByLabelText("Pregunta")).toBeInTheDocument();
  });

  it("submits a question and shows the response", async () => {
    mockedPostQuery.mockResolvedValueOnce(mockQueryResponse);
    const user = userEvent.setup();
    render(<QueryDashboard />);

    await user.type(screen.getByLabelText("Pregunta"), "¿Cuál es el promedio?");
    await user.click(screen.getByLabelText("Enviar consulta"));

    await waitFor(() => {
      expect(
        screen.getByText("El docente tiene un promedio de 4.5."),
      ).toBeInTheDocument();
    });

    expect(mockedPostQuery).toHaveBeenCalledWith(
      {
        question: "¿Cuál es el promedio?",
        filters: { modalidad: "CUATRIMESTRAL" },
      },
      expect.any(AbortSignal),
    );
  });

  it("shows evidence after a successful query", async () => {
    mockedPostQuery.mockResolvedValueOnce(mockQueryResponse);
    const user = userEvent.setup();
    render(<QueryDashboard />);

    await user.type(screen.getByLabelText("Pregunta"), "Pregunta");
    await user.click(screen.getByLabelText("Enviar consulta"));

    await waitFor(() => {
      expect(screen.getByText("Evidencias recuperadas")).toBeInTheDocument();
    });

    expect(screen.getByText("Promedio general")).toBeInTheDocument();
    expect(screen.getByText("Excelente docente.")).toBeInTheDocument();
  });

  it("shows error state on failure", async () => {
    mockedPostQuery.mockRejectedValueOnce(
      new Error("API error: 502 Bad Gateway"),
    );
    const user = userEvent.setup();
    render(<QueryDashboard />);

    await user.type(screen.getByLabelText("Pregunta"), "Pregunta");
    await user.click(screen.getByLabelText("Enviar consulta"));

    await waitFor(() => {
      expect(
        screen.getByText("API error: 502 Bad Gateway"),
      ).toBeInTheDocument();
    });
  });

  it("adds question to history after successful query", async () => {
    mockedPostQuery.mockResolvedValueOnce(mockQueryResponse);
    const user = userEvent.setup();
    render(<QueryDashboard />);

    await user.type(screen.getByLabelText("Pregunta"), "¿Cuál es el promedio?");
    await user.click(screen.getByLabelText("Enviar consulta"));

    await waitFor(() => {
      expect(screen.getByText("Historial de consultas")).toBeInTheDocument();
    });

    expect(screen.getByText("¿Cuál es el promedio?")).toBeInTheDocument();
  });

  it("shows loading skeleton while fetching", async () => {
    let resolveQuery: (value: QueryResponse) => void;
    mockedPostQuery.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolveQuery = resolve;
        }),
    );
    const user = userEvent.setup();
    const { container } = render(<QueryDashboard />);

    await user.type(screen.getByLabelText("Pregunta"), "Test");
    await user.click(screen.getByLabelText("Enviar consulta"));

    expect(container.querySelectorAll(".animate-pulse").length).toBeGreaterThan(
      0,
    );

    resolveQuery!(mockQueryResponse);
    await waitFor(() => {
      expect(container.querySelectorAll(".animate-pulse").length).toBe(0);
    });
  });
});
