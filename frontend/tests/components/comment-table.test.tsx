import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { CommentTable } from "@/components/sentimiento/comment-table";
import type { ComentarioAnalisis } from "@/types";

const mockComments: ComentarioAnalisis[] = [
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

describe("CommentTable", () => {
  it("renders comment texts", () => {
    render(<CommentTable data={mockComments} />);
    expect(
      screen.getByText(/Excelente profesor, muy claro/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Debería mejorar la puntualidad/),
    ).toBeInTheDocument();
  });

  it("renders badges for tipo, tema, and sentimiento", () => {
    render(<CommentTable data={mockComments} />);
    expect(screen.getByText("Fortaleza")).toBeInTheDocument();
    expect(screen.getByText("Mejora")).toBeInTheDocument();
    expect(screen.getByText("Comunicación")).toBeInTheDocument();
    expect(screen.getByText("Puntualidad")).toBeInTheDocument();
    expect(screen.getByText("Positivo")).toBeInTheDocument();
    expect(screen.getByText("Negativo")).toBeInTheDocument();
  });

  it("renders fuente column", () => {
    render(<CommentTable data={mockComments} />);
    expect(screen.getByText("Estudiante")).toBeInTheDocument();
    expect(screen.getByText("Director")).toBeInTheDocument();
  });

  it("renders asignatura below comment text", () => {
    render(<CommentTable data={mockComments} />);
    expect(screen.getByText("Programación I")).toBeInTheDocument();
    expect(screen.getByText("Base de datos")).toBeInTheDocument();
  });

  it("shows count in header description", () => {
    render(<CommentTable data={mockComments} />);
    expect(screen.getByText("2 comentarios mostrados.")).toBeInTheDocument();
  });

  it("shows empty state when no data", () => {
    render(<CommentTable data={[]} />);
    expect(
      screen.getByText("No hay comentarios que coincidan con los filtros."),
    ).toBeInTheDocument();
  });

  it("renders table headers", () => {
    render(<CommentTable data={mockComments} />);
    expect(screen.getByText("Comentario")).toBeInTheDocument();
    expect(screen.getByText("Tipo")).toBeInTheDocument();
    expect(screen.getByText("Tema")).toBeInTheDocument();
    expect(screen.getByText("Sentimiento")).toBeInTheDocument();
    expect(screen.getByText("Fuente")).toBeInTheDocument();
  });
});
