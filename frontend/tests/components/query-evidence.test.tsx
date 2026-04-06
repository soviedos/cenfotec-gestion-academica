import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryEvidenceList } from "@/components/consultas-ia/query-evidence";
import type { QueryEvidence } from "@/types";

const mockEvidence: QueryEvidence[] = [
  {
    type: "metric",
    label: "Promedio general",
    value: 4.52,
    source: { periodo: "2025-1", docente: "Prof. López" },
  },
  {
    type: "comment",
    texto: "Muy buena metodología de enseñanza.",
    source: {
      evaluacion_id: "e1",
      docente: "Prof. García",
      periodo: "2025-1",
      asignatura: "Base de datos",
      fuente: "Estudiante",
    },
    relevance_score: 0.8,
  },
];

describe("QueryEvidenceList", () => {
  it("renders nothing when evidence is empty", () => {
    const { container } = render(<QueryEvidenceList evidence={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders metric evidence with label and value", () => {
    render(<QueryEvidenceList evidence={mockEvidence} />);
    expect(screen.getByText("Promedio general")).toBeInTheDocument();
    expect(screen.getByText("4.52")).toBeInTheDocument();
  });

  it("renders comment evidence with text and badges", () => {
    render(<QueryEvidenceList evidence={mockEvidence} />);
    expect(
      screen.getByText("Muy buena metodología de enseñanza."),
    ).toBeInTheDocument();
    expect(screen.getByText("Prof. García")).toBeInTheDocument();
    expect(screen.getByText("Base de datos")).toBeInTheDocument();
    expect(screen.getByText("Estudiante")).toBeInTheDocument();
  });

  it("renders section headers", () => {
    render(<QueryEvidenceList evidence={mockEvidence} />);
    expect(screen.getByText("Métricas")).toBeInTheDocument();
    expect(screen.getByText("Comentarios")).toBeInTheDocument();
  });

  it("hides Métricas section when no metrics", () => {
    const onlyComments = mockEvidence.filter((e) => e.type === "comment");
    render(<QueryEvidenceList evidence={onlyComments} />);
    expect(screen.queryByText("Métricas")).not.toBeInTheDocument();
    expect(screen.getByText("Comentarios")).toBeInTheDocument();
  });
});
