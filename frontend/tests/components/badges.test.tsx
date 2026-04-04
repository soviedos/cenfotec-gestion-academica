import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  SentimentBadge,
  TipoBadge,
  TemaBadge,
  temaLabel,
} from "@/components/sentimiento/badges";

describe("SentimentBadge", () => {
  it("renders positivo badge with correct text", () => {
    render(<SentimentBadge value="positivo" />);
    expect(screen.getByText("Positivo")).toBeInTheDocument();
  });

  it("renders negativo badge", () => {
    render(<SentimentBadge value="negativo" />);
    expect(screen.getByText("Negativo")).toBeInTheDocument();
  });

  it("renders neutro badge", () => {
    render(<SentimentBadge value="neutro" />);
    expect(screen.getByText("Neutro")).toBeInTheDocument();
  });

  it("renders mixto badge", () => {
    render(<SentimentBadge value="mixto" />);
    expect(screen.getByText("Mixto")).toBeInTheDocument();
  });

  it("renders dash for null value", () => {
    render(<SentimentBadge value={null} />);
    expect(screen.getByText("—")).toBeInTheDocument();
  });
});

describe("TipoBadge", () => {
  it("renders fortaleza badge", () => {
    render(<TipoBadge value="fortaleza" />);
    expect(screen.getByText("Fortaleza")).toBeInTheDocument();
  });

  it("renders mejora badge", () => {
    render(<TipoBadge value="mejora" />);
    expect(screen.getByText("Mejora")).toBeInTheDocument();
  });

  it("renders observacion badge", () => {
    render(<TipoBadge value="observacion" />);
    expect(screen.getByText("Observación")).toBeInTheDocument();
  });

  it("renders raw value for unknown tipo", () => {
    render(<TipoBadge value="desconocido" />);
    expect(screen.getByText("desconocido")).toBeInTheDocument();
  });
});

describe("TemaBadge", () => {
  it("renders translated tema label", () => {
    render(<TemaBadge value="metodologia" />);
    expect(screen.getByText("Metodología")).toBeInTheDocument();
  });

  it("renders raw value for unknown tema", () => {
    render(<TemaBadge value="custom_tema" />);
    expect(screen.getByText("custom_tema")).toBeInTheDocument();
  });
});

describe("temaLabel", () => {
  it("returns translated label for known tema", () => {
    expect(temaLabel("comunicacion")).toBe("Comunicación");
  });

  it("returns raw value for unknown tema", () => {
    expect(temaLabel("xyz")).toBe("xyz");
  });
});
