import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PaginationBar } from "@/components/biblioteca/pagination-bar";

describe("PaginationBar", () => {
  const defaultProps = {
    page: 1,
    pageSize: 20,
    total: 100,
    totalPages: 5,
    onPageChange: vi.fn(),
  };

  it("displays current range and total", () => {
    render(<PaginationBar {...defaultProps} />);
    expect(screen.getByText(/Mostrando/)).toHaveTextContent(
      /Mostrando 1 a 20 de 100 documentos/,
    );
  });

  it("displays page info", () => {
    render(<PaginationBar {...defaultProps} page={3} />);
    expect(screen.getByText(/Página/)).toHaveTextContent(/Página 3 de 5/);
  });

  it("shows 'Sin resultados' when total is 0", () => {
    render(<PaginationBar {...defaultProps} total={0} totalPages={1} />);
    expect(screen.getByText("Sin resultados")).toBeInTheDocument();
  });

  it("disables previous buttons on first page", () => {
    render(<PaginationBar {...defaultProps} page={1} />);
    expect(screen.getByLabelText("Primera página")).toBeDisabled();
    expect(screen.getByLabelText("Página anterior")).toBeDisabled();
    expect(screen.getByLabelText("Página siguiente")).not.toBeDisabled();
    expect(screen.getByLabelText("Última página")).not.toBeDisabled();
  });

  it("disables next buttons on last page", () => {
    render(<PaginationBar {...defaultProps} page={5} />);
    expect(screen.getByLabelText("Primera página")).not.toBeDisabled();
    expect(screen.getByLabelText("Página anterior")).not.toBeDisabled();
    expect(screen.getByLabelText("Página siguiente")).toBeDisabled();
    expect(screen.getByLabelText("Última página")).toBeDisabled();
  });

  it("calls onPageChange with correct page on next click", async () => {
    const user = userEvent.setup();
    const onPageChange = vi.fn();
    render(<PaginationBar {...defaultProps} page={2} onPageChange={onPageChange} />);

    await user.click(screen.getByLabelText("Página siguiente"));
    expect(onPageChange).toHaveBeenCalledWith(3);
  });

  it("calls onPageChange with correct page on previous click", async () => {
    const user = userEvent.setup();
    const onPageChange = vi.fn();
    render(<PaginationBar {...defaultProps} page={3} onPageChange={onPageChange} />);

    await user.click(screen.getByLabelText("Página anterior"));
    expect(onPageChange).toHaveBeenCalledWith(2);
  });

  it("calls onPageChange with 1 on first page click", async () => {
    const user = userEvent.setup();
    const onPageChange = vi.fn();
    render(<PaginationBar {...defaultProps} page={3} onPageChange={onPageChange} />);

    await user.click(screen.getByLabelText("Primera página"));
    expect(onPageChange).toHaveBeenCalledWith(1);
  });

  it("calls onPageChange with totalPages on last page click", async () => {
    const user = userEvent.setup();
    const onPageChange = vi.fn();
    render(<PaginationBar {...defaultProps} page={2} onPageChange={onPageChange} />);

    await user.click(screen.getByLabelText("Última página"));
    expect(onPageChange).toHaveBeenCalledWith(5);
  });

  it("disables all buttons when isLoading", () => {
    render(<PaginationBar {...defaultProps} page={3} isLoading={true} />);
    expect(screen.getByLabelText("Primera página")).toBeDisabled();
    expect(screen.getByLabelText("Página anterior")).toBeDisabled();
    expect(screen.getByLabelText("Página siguiente")).toBeDisabled();
    expect(screen.getByLabelText("Última página")).toBeDisabled();
  });

  it("has navigation role for accessibility", () => {
    render(<PaginationBar {...defaultProps} />);
    expect(screen.getByRole("navigation", { name: "Paginación" })).toBeInTheDocument();
  });
});
