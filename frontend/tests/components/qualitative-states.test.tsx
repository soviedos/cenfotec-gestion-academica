import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  QualitativeSkeleton,
  QualitativeEmpty,
  QualitativeError,
} from "@/components/sentimiento/qualitative-states";

describe("QualitativeSkeleton", () => {
  it("renders skeleton placeholders", () => {
    const { container } = render(<QualitativeSkeleton />);
    const pulseElements = container.querySelectorAll(".animate-pulse");
    expect(pulseElements.length).toBe(8);
  });
});

describe("QualitativeEmpty", () => {
  it("renders empty state message", () => {
    render(<QualitativeEmpty />);
    expect(screen.getByText("Sin comentarios analizados")).toBeInTheDocument();
    expect(
      screen.getByText(/Suba y procese evaluaciones docentes/),
    ).toBeInTheDocument();
  });
});

describe("QualitativeError", () => {
  it("renders error message and retry button", () => {
    const onRetry = () => {};
    render(<QualitativeError message="Error de conexión" onRetry={onRetry} />);
    expect(screen.getByText("Error de conexión")).toBeInTheDocument();
    expect(screen.getByText("Reintentar")).toBeInTheDocument();
  });

  it("calls onRetry when button clicked", async () => {
    const { default: userEvent } = await import("@testing-library/user-event");
    const onRetry = vi.fn();
    render(
      <QualitativeError message="Error" onRetry={onRetry} />,
    );
    const user = userEvent.setup();
    await user.click(screen.getByText("Reintentar"));
    expect(onRetry).toHaveBeenCalledOnce();
  });
});
