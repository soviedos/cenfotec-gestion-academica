import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryInput } from "@/components/consultas-ia/query-input";

describe("QueryInput", () => {
  it("renders textarea and submit button", () => {
    render(<QueryInput onSubmit={() => {}} isLoading={false} />);
    expect(screen.getByLabelText("Pregunta")).toBeInTheDocument();
    expect(screen.getByLabelText("Enviar consulta")).toBeInTheDocument();
  });

  it("calls onSubmit with trimmed question", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<QueryInput onSubmit={onSubmit} isLoading={false} />);

    await user.type(
      screen.getByLabelText("Pregunta"),
      "  ¿Cómo son los docentes?  ",
    );
    await user.click(screen.getByLabelText("Enviar consulta"));

    expect(onSubmit).toHaveBeenCalledWith("¿Cómo son los docentes?");
  });

  it("clears input after submit", async () => {
    const user = userEvent.setup();
    render(<QueryInput onSubmit={() => {}} isLoading={false} />);

    const textarea = screen.getByLabelText("Pregunta");
    await user.type(textarea, "Pregunta de prueba");
    await user.click(screen.getByLabelText("Enviar consulta"));

    expect(textarea).toHaveValue("");
  });

  it("submits on Enter (without Shift)", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<QueryInput onSubmit={onSubmit} isLoading={false} />);

    await user.type(screen.getByLabelText("Pregunta"), "Test{Enter}");
    expect(onSubmit).toHaveBeenCalledWith("Test");
  });

  it("does not submit on Shift+Enter", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<QueryInput onSubmit={onSubmit} isLoading={false} />);

    await user.type(
      screen.getByLabelText("Pregunta"),
      "Test{Shift>}{Enter}{/Shift}",
    );
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("disables button when loading", () => {
    render(<QueryInput onSubmit={() => {}} isLoading={true} />);
    expect(screen.getByLabelText("Enviar consulta")).toBeDisabled();
  });

  it("disables button when input is empty", () => {
    render(<QueryInput onSubmit={() => {}} isLoading={false} />);
    expect(screen.getByLabelText("Enviar consulta")).toBeDisabled();
  });

  it("does not submit empty question", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<QueryInput onSubmit={onSubmit} isLoading={false} />);

    await user.type(screen.getByLabelText("Pregunta"), "   ");
    await user.click(screen.getByLabelText("Enviar consulta"));

    expect(onSubmit).not.toHaveBeenCalled();
  });
});
