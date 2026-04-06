import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  QuerySkeleton,
  QueryError,
} from "@/components/consultas-ia/query-states";

describe("QuerySkeleton", () => {
  it("renders skeleton placeholders", () => {
    const { container } = render(<QuerySkeleton />);
    const pulseElements = container.querySelectorAll(".animate-pulse");
    expect(pulseElements.length).toBe(2);
  });
});

describe("QueryError", () => {
  it("renders error message and retry button", () => {
    render(<QueryError message="Error de conexión" onRetry={() => {}} />);
    expect(screen.getByText("Error de conexión")).toBeInTheDocument();
    expect(screen.getByText("Reintentar")).toBeInTheDocument();
  });

  it("calls onRetry when button is clicked", async () => {
    const onRetry = vi.fn();
    const user = userEvent.setup();
    render(<QueryError message="Error" onRetry={onRetry} />);

    await user.click(screen.getByText("Reintentar"));
    expect(onRetry).toHaveBeenCalledOnce();
  });
});
