import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DocumentLibrary } from "@/components/biblioteca/document-library";
import type { Documento, PaginatedResponse } from "@/types";

// Mock the API module
vi.mock("@/lib/api/documents", () => ({
  listDocuments: vi.fn(),
}));

import { listDocuments } from "@/lib/api/documents";

const mockListDocuments = vi.mocked(listDocuments);

function makeResponse(
  items: Partial<Documento>[] = [],
  overrides: Partial<PaginatedResponse<Documento>> = {},
): PaginatedResponse<Documento> {
  const docs: Documento[] = items.map((item, i) => ({
    id: `id-${i}`,
    nombre_archivo: `doc_${i}.pdf`,
    hash_sha256: `hash_${i}`,
    estado: "subido",
    storage_path: `docs/${i}.pdf`,
    tamano_bytes: 1024,
    error_detalle: null,
    created_at: "2025-06-15T10:30:00Z",
    updated_at: "2025-06-15T10:30:00Z",
    ...item,
  }));
  return {
    items: docs,
    total: docs.length,
    page: 1,
    page_size: 20,
    total_pages: 1,
    ...overrides,
  };
}

describe("DocumentLibrary", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading state initially", () => {
    mockListDocuments.mockReturnValue(new Promise(() => {})); // never resolves
    render(<DocumentLibrary />);
    expect(screen.getByText("Cargando documentos...")).toBeInTheDocument();
  });

  it("renders documents after successful fetch", async () => {
    mockListDocuments.mockResolvedValue(
      makeResponse([
        { nombre_archivo: "evaluacion_2025.pdf", tamano_bytes: 2048 },
        { nombre_archivo: "reporte_docente.pdf", tamano_bytes: 5120 },
      ]),
    );

    render(<DocumentLibrary />);

    await waitFor(() => {
      expect(screen.getByText("evaluacion_2025.pdf")).toBeInTheDocument();
    });
    expect(screen.getByText("reporte_docente.pdf")).toBeInTheDocument();
  });

  it("shows total count badge", async () => {
    mockListDocuments.mockResolvedValue(
      makeResponse(
        [{ nombre_archivo: "doc.pdf" }],
        { total: 42, total_pages: 3 },
      ),
    );

    render(<DocumentLibrary />);

    await waitFor(() => {
      expect(screen.getByText("doc.pdf")).toBeInTheDocument();
    });
    // Badge with data-slot="badge" shows total count next to title
    const badge = screen.getByText("42", { selector: "[data-slot='badge']" });
    expect(badge).toBeInTheDocument();
  });

  it("renders error state", async () => {
    mockListDocuments.mockRejectedValue(new Error("Network error"));

    render(<DocumentLibrary />);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
    expect(screen.getByText("Network error")).toBeInTheDocument();
  });

  it("renders empty state when no documents", async () => {
    mockListDocuments.mockResolvedValue(makeResponse([]));

    render(<DocumentLibrary />);

    await waitFor(() => {
      expect(screen.getByText("No se encontraron documentos")).toBeInTheDocument();
    });
  });

  it("renders filter controls", async () => {
    mockListDocuments.mockResolvedValue(makeResponse([]));

    render(<DocumentLibrary />);

    await waitFor(() => {
      expect(screen.getByLabelText("Buscar por nombre de archivo")).toBeInTheDocument();
    });
    expect(screen.getByLabelText("Filtrar por docente")).toBeInTheDocument();
    expect(screen.getByLabelText("Filtrar por estado")).toBeInTheDocument();
  });

  it("renders pagination", async () => {
    mockListDocuments.mockResolvedValue(
      makeResponse(
        [{ nombre_archivo: "doc.pdf" }],
        { total: 50, page: 1, page_size: 20, total_pages: 3 },
      ),
    );

    render(<DocumentLibrary />);

    await waitFor(() => {
      expect(screen.getByRole("navigation", { name: "Paginación" })).toBeInTheDocument();
    });
  });

  it("has a reload button", async () => {
    mockListDocuments.mockResolvedValue(makeResponse([]));

    render(<DocumentLibrary />);

    await waitFor(() => {
      expect(screen.getByLabelText("Recargar documentos")).toBeInTheDocument();
    });
  });

  it("calls API on reload click", async () => {
    const user = userEvent.setup();
    mockListDocuments.mockResolvedValue(makeResponse([]));

    render(<DocumentLibrary />);

    await waitFor(() => {
      expect(mockListDocuments).toHaveBeenCalledTimes(1);
    });

    await user.click(screen.getByLabelText("Recargar documentos"));

    await waitFor(() => {
      expect(mockListDocuments).toHaveBeenCalledTimes(2);
    });
  });

  it("renders the page header content", async () => {
    mockListDocuments.mockResolvedValue(makeResponse([]));

    render(<DocumentLibrary />);

    expect(screen.getByText("Documentos")).toBeInTheDocument();
    expect(
      screen.getByText(/Biblioteca de PDFs de evaluaciones docentes/),
    ).toBeInTheDocument();
  });
});
