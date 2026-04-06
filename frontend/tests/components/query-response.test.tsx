import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryResponseCard } from "@/components/consultas-ia/query-response";
import type { QueryResponse } from "@/types";

const mockResponse: QueryResponse = {
  answer: "El docente tiene un desempeño destacado en comunicación.",
  confidence: 0.85,
  evidence: [
    {
      type: "metric",
      label: "Promedio general",
      value: 4.5,
      source: { periodo: "2025-1", docente: "Prof. López" },
    },
    {
      type: "comment",
      texto: "Excelente comunicación en clase.",
      source: {
        evaluacion_id: "e1",
        docente: "Prof. López",
        periodo: "2025-1",
        asignatura: "Programación I",
        fuente: "Estudiante",
      },
      relevance_score: 0.9,
    },
  ],
  metadata: {
    model: "gemini-2.0-flash",
    tokens_used: 350,
    latency_ms: 1200,
    audit_log_id: "a1",
  },
};

describe("QueryResponseCard", () => {
  it("renders the answer text", () => {
    render(<QueryResponseCard response={mockResponse} />);
    expect(
      screen.getByText(
        "El docente tiene un desempeño destacado en comunicación.",
      ),
    ).toBeInTheDocument();
  });

  it("shows confidence badge", () => {
    render(<QueryResponseCard response={mockResponse} />);
    expect(screen.getByText("Confianza: 85%")).toBeInTheDocument();
  });

  it("shows model name badge", () => {
    render(<QueryResponseCard response={mockResponse} />);
    expect(screen.getByText("gemini-2.0-flash")).toBeInTheDocument();
  });

  it("shows metadata stats", () => {
    render(<QueryResponseCard response={mockResponse} />);
    expect(screen.getByText("350 tokens")).toBeInTheDocument();
    expect(screen.getByText("1200ms")).toBeInTheDocument();
    expect(screen.getByText("2 evidencias")).toBeInTheDocument();
  });

  it("hides confidence badge when null", () => {
    const noConfidence = { ...mockResponse, confidence: null };
    render(<QueryResponseCard response={noConfidence} />);
    expect(screen.queryByText(/Confianza/)).not.toBeInTheDocument();
  });
});
