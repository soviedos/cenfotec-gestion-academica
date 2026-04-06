import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryHistory } from "@/components/consultas-ia/query-history";
import type { QueryHistoryEntry, QueryResponse } from "@/types";

const baseResponse: QueryResponse = {
  answer: "Respuesta de prueba",
  confidence: 0.8,
  evidence: [],
  metadata: {
    model: "gemini-2.0-flash",
    tokens_used: 100,
    latency_ms: 500,
    audit_log_id: "a1",
  },
};

const mockHistory: QueryHistoryEntry[] = [
  {
    question: "¿Cuáles son los mejores docentes?",
    response: baseResponse,
    timestamp: new Date("2025-06-05T10:30:00"),
  },
  {
    question: "¿Cómo está la comunicación?",
    response: baseResponse,
    timestamp: new Date("2025-06-05T10:25:00"),
  },
];

describe("QueryHistory", () => {
  it("renders nothing when history is empty", () => {
    const { container } = render(
      <QueryHistory history={[]} onSelect={() => {}} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders history entries", () => {
    render(<QueryHistory history={mockHistory} onSelect={() => {}} />);
    expect(
      screen.getByText("¿Cuáles son los mejores docentes?"),
    ).toBeInTheDocument();
    expect(screen.getByText("¿Cómo está la comunicación?")).toBeInTheDocument();
  });

  it("calls onSelect when entry is clicked", async () => {
    const onSelect = vi.fn();
    const user = userEvent.setup();
    render(<QueryHistory history={mockHistory} onSelect={onSelect} />);

    await user.click(screen.getByText("¿Cuáles son los mejores docentes?"));
    expect(onSelect).toHaveBeenCalledWith("¿Cuáles son los mejores docentes?");
  });

  it("shows the title with clock icon", () => {
    render(<QueryHistory history={mockHistory} onSelect={() => {}} />);
    expect(screen.getByText("Historial de consultas")).toBeInTheDocument();
  });
});
