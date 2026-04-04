import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DocumentFilters } from "@/components/biblioteca/document-filters";

describe("DocumentFilters", () => {
  it("renders all filter inputs", () => {
    render(<DocumentFilters onFilterChange={vi.fn()} />);

    expect(screen.getByLabelText("Buscar por nombre de archivo")).toBeInTheDocument();
    expect(screen.getByLabelText("Filtrar por docente")).toBeInTheDocument();
    expect(screen.getByLabelText("Filtrar por periodo")).toBeInTheDocument();
    expect(screen.getByLabelText("Filtrar por estado")).toBeInTheDocument();
  });

  it("calls onFilterChange on estado select", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<DocumentFilters onFilterChange={onChange} />);

    const select = screen.getByLabelText("Filtrar por estado");
    await user.selectOptions(select, "procesado");

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ estado: "procesado" }),
    );
  });

  it("shows clear button when filters are active", async () => {
    const user = userEvent.setup();
    render(<DocumentFilters onFilterChange={vi.fn()} />);

    // No clear button initially
    expect(screen.queryByLabelText("Limpiar filtros")).not.toBeInTheDocument();

    // Type in search to activate filters
    const select = screen.getByLabelText("Filtrar por estado");
    await user.selectOptions(select, "subido");

    expect(screen.getByLabelText("Limpiar filtros")).toBeInTheDocument();
  });

  it("clears all filters when clear button is clicked", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<DocumentFilters onFilterChange={onChange} />);

    // Set a filter first
    const select = screen.getByLabelText("Filtrar por estado");
    await user.selectOptions(select, "subido");
    onChange.mockClear();

    // Click clear
    await user.click(screen.getByLabelText("Limpiar filtros"));

    expect(onChange).toHaveBeenCalledWith({});
    expect(screen.queryByLabelText("Limpiar filtros")).not.toBeInTheDocument();
  });

  it("disables inputs when isLoading is true", () => {
    render(<DocumentFilters onFilterChange={vi.fn()} isLoading={true} />);

    expect(screen.getByLabelText("Buscar por nombre de archivo")).toBeDisabled();
    expect(screen.getByLabelText("Filtrar por docente")).toBeDisabled();
    expect(screen.getByLabelText("Filtrar por periodo")).toBeDisabled();
    expect(screen.getByLabelText("Filtrar por estado")).toBeDisabled();
  });

  it("has search role for accessibility", () => {
    render(<DocumentFilters onFilterChange={vi.fn()} />);
    expect(screen.getByRole("search", { name: "Filtros de documentos" })).toBeInTheDocument();
  });

  it("debounces text input changes", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<DocumentFilters onFilterChange={onChange} />);

    const input = screen.getByLabelText("Buscar por nombre de archivo");
    await user.type(input, "test");

    // After typing + debounce, should eventually fire
    await vi.waitFor(() => {
      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ nombre_archivo: "test" }),
      );
    }, { timeout: 1000 });
  });
});
