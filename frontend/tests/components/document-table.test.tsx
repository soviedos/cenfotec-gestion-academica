import { describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DocumentTable } from "@/features/evaluacion-docente/components/biblioteca/document-table";
import type { Documento } from "@/features/evaluacion-docente/types";

const mockSort = vi.fn();
const mockRowSelectionChange = vi.fn();

const selectionProps = {
  rowSelection: {} as Record<string, boolean>,
  onRowSelectionChange: mockRowSelectionChange,
};

function makeDoc(overrides: Partial<Documento> = {}): Documento {
  const id = crypto.randomUUID();
  return {
    id,
    nombre_archivo: `evaluacion_${id.slice(0, 4)}.pdf`,
    hash_sha256: "abc123",
    estado: "subido",
    storage_path: `documentos/${id}.pdf`,
    tamano_bytes: 1024,
    error_detalle: null,
    content_fingerprint: null,
    posible_duplicado: false,
    comentarios_total: 0,
    comentarios_ia: 0,
    created_at: "2025-06-15T10:30:00Z",
    updated_at: "2025-06-15T10:30:00Z",
    ...overrides,
  };
}

describe("DocumentTable", () => {
  it("renders loading state", () => {
    render(
      <DocumentTable
        data={[]}
        isLoading={true}
        isEmpty={false}
        sortBy="created_at"
        sortOrder="desc"
        onSort={mockSort}
        {...selectionProps}
      />,
    );
    expect(screen.getByText("Cargando documentos...")).toBeInTheDocument();
  });

  it("renders empty state", () => {
    render(
      <DocumentTable
        data={[]}
        isLoading={false}
        isEmpty={true}
        sortBy="created_at"
        sortOrder="desc"
        onSort={mockSort}
        {...selectionProps}
      />,
    );
    expect(
      screen.getByText("No se encontraron documentos"),
    ).toBeInTheDocument();
  });

  it("renders document rows", () => {
    const docs = [
      makeDoc({ nombre_archivo: "reporte_q1.pdf", tamano_bytes: 2048 }),
      makeDoc({ nombre_archivo: "reporte_q2.pdf", tamano_bytes: 5120 }),
    ];

    render(
      <DocumentTable
        data={docs}
        isLoading={false}
        isEmpty={false}
        sortBy="created_at"
        sortOrder="desc"
        onSort={mockSort}
        {...selectionProps}
      />,
    );

    expect(screen.getByText("reporte_q1.pdf")).toBeInTheDocument();
    expect(screen.getByText("reporte_q2.pdf")).toBeInTheDocument();
    expect(screen.getByText("2.0 KB")).toBeInTheDocument();
    expect(screen.getByText("5.0 KB")).toBeInTheDocument();
  });

  it("renders estado badges for each status", () => {
    const docs = [
      makeDoc({ estado: "subido" }),
      makeDoc({ estado: "procesando" }),
      makeDoc({ estado: "procesado" }),
      makeDoc({ estado: "error" }),
    ];

    render(
      <DocumentTable
        data={docs}
        isLoading={false}
        isEmpty={false}
        sortBy="created_at"
        sortOrder="desc"
        onSort={mockSort}
        {...selectionProps}
      />,
    );

    const badges = screen.getAllByTestId("estado-badge");
    const labels = badges.map((b) => b.textContent);
    expect(labels).toContain("Subido");
    expect(labels).toContain("Procesando");
    expect(labels).toContain("Procesado");
    expect(labels).toContain("Error");
  });

  it("calls onSort when clicking sortable header", async () => {
    const user = userEvent.setup();
    render(
      <DocumentTable
        data={[makeDoc()]}
        isLoading={false}
        isEmpty={false}
        sortBy="created_at"
        sortOrder="desc"
        onSort={mockSort}
        {...selectionProps}
      />,
    );

    const sortButton = screen.getByRole("button", {
      name: /Ordenar por Nombre/i,
    });
    await user.click(sortButton);
    expect(mockSort).toHaveBeenCalledWith("nombre_archivo");
  });

  it("renders table headers", () => {
    render(
      <DocumentTable
        data={[]}
        isLoading={false}
        isEmpty={true}
        sortBy="created_at"
        sortOrder="desc"
        onSort={mockSort}
        {...selectionProps}
      />,
    );

    expect(
      screen.getByRole("button", { name: /Ordenar por Nombre/i }),
    ).toBeInTheDocument();
    expect(screen.getByText("Estado")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Ordenar por Tamaño/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Ordenar por Fecha de carga/i }),
    ).toBeInTheDocument();
  });

  it("renders duplicado badge for duplicate documents", () => {
    const docs = [
      makeDoc({ posible_duplicado: true }),
      makeDoc({ posible_duplicado: false }),
    ];
    render(
      <DocumentTable
        data={docs}
        isLoading={false}
        isEmpty={false}
        sortBy="created_at"
        sortOrder="desc"
        onSort={mockSort}
        {...selectionProps}
      />,
    );

    const badges = screen.getAllByTestId("duplicado-badge");
    expect(badges).toHaveLength(1);
  });

  it("does not render duplicado badge when no documents are duplicates", () => {
    render(
      <DocumentTable
        data={[makeDoc(), makeDoc()]}
        isLoading={false}
        isEmpty={false}
        sortBy="created_at"
        sortOrder="desc"
        onSort={mockSort}
        {...selectionProps}
      />,
    );

    expect(screen.queryByTestId("duplicado-badge")).not.toBeInTheDocument();
  });
});
