import { describe, expect, it } from "vitest";
import {
  comparePeriodos,
  parsePeriodoKey,
  sortByPeriodo,
} from "@/lib/periodo-sort";

// ════════════════════════════════════════════════════════════════
//  parsePeriodoKey
// ════════════════════════════════════════════════════════════════

describe("parsePeriodoKey", () => {
  it("parses cuatrimestral C2 2025", () => {
    expect(parsePeriodoKey("C2 2025")).toEqual({
      año: 2025,
      prefijo: "C",
      numero: 2,
    });
  });

  it("parses cuatrimestral case-insensitive", () => {
    expect(parsePeriodoKey("c1 2024")).toEqual({
      año: 2024,
      prefijo: "C",
      numero: 1,
    });
  });

  it("parses mensual M10 2024", () => {
    expect(parsePeriodoKey("M10 2024")).toEqual({
      año: 2024,
      prefijo: "M",
      numero: 10,
    });
  });

  it("parses MT3 2026", () => {
    expect(parsePeriodoKey("MT3 2026")).toEqual({
      año: 2026,
      prefijo: "MT",
      numero: 3,
    });
  });

  it("parses B2B with year", () => {
    const key = parsePeriodoKey("B2B 2025");
    expect(key.prefijo).toBe("B2B");
    expect(key.año).toBe(2025);
  });

  it("returns fallback for unparseable string", () => {
    expect(parsePeriodoKey("garbage")).toEqual({
      año: 9999,
      prefijo: "ZZZ",
      numero: 0,
    });
  });

  it("returns fallback for empty string", () => {
    expect(parsePeriodoKey("")).toEqual({
      año: 9999,
      prefijo: "ZZZ",
      numero: 0,
    });
  });
});

// ════════════════════════════════════════════════════════════════
//  comparePeriodos
// ════════════════════════════════════════════════════════════════

describe("comparePeriodos", () => {
  it("sorts by year first", () => {
    expect(comparePeriodos("C1 2024", "C1 2025")).toBeLessThan(0);
    expect(comparePeriodos("C1 2025", "C1 2024")).toBeGreaterThan(0);
  });

  it("sorts by prefix within same year", () => {
    // "C" < "M"
    expect(comparePeriodos("C1 2024", "M1 2024")).toBeLessThan(0);
  });

  it("sorts by numero within same year and prefix", () => {
    expect(comparePeriodos("C1 2024", "C3 2024")).toBeLessThan(0);
    expect(comparePeriodos("C3 2024", "C1 2024")).toBeGreaterThan(0);
  });

  it("returns 0 for identical periods", () => {
    expect(comparePeriodos("C2 2025", "C2 2025")).toBe(0);
  });

  it("cross-year: C3 2024 before C1 2025", () => {
    expect(comparePeriodos("C3 2024", "C1 2025")).toBeLessThan(0);
  });

  it("unparseable sorts after valid", () => {
    expect(comparePeriodos("C1 2024", "garbage")).toBeLessThan(0);
  });
});

// ════════════════════════════════════════════════════════════════
//  sortByPeriodo
// ════════════════════════════════════════════════════════════════

describe("sortByPeriodo", () => {
  it("sorts cuatrimestral within year", () => {
    const items = [
      { periodo: "C3 2024", v: 3 },
      { periodo: "C1 2024", v: 1 },
      { periodo: "C2 2024", v: 2 },
    ];
    const sorted = sortByPeriodo(items);
    expect(sorted.map((r) => r.periodo)).toEqual([
      "C1 2024",
      "C2 2024",
      "C3 2024",
    ]);
  });

  it("sorts cross-year correctly [BR-AN-42]", () => {
    const items = [
      { periodo: "C1 2025" },
      { periodo: "C3 2024" },
      { periodo: "C2 2025" },
      { periodo: "C1 2024" },
    ];
    const sorted = sortByPeriodo(items);
    expect(sorted.map((r) => r.periodo)).toEqual([
      "C1 2024",
      "C3 2024",
      "C1 2025",
      "C2 2025",
    ]);
  });

  it("sorts mensual correctly", () => {
    const items = [
      { periodo: "M10 2024" },
      { periodo: "M1 2024" },
      { periodo: "M5 2024" },
    ];
    const sorted = sortByPeriodo(items);
    expect(sorted.map((r) => r.periodo)).toEqual([
      "M1 2024",
      "M5 2024",
      "M10 2024",
    ]);
  });

  it("handles empty array", () => {
    expect(sortByPeriodo([])).toEqual([]);
  });

  it("does not mutate original array", () => {
    const items = [{ periodo: "C2 2024" }, { periodo: "C1 2024" }];
    sortByPeriodo(items);
    expect(items[0].periodo).toBe("C2 2024");
  });

  it("pushes unparseable to end", () => {
    const items = [
      { periodo: "garbage" },
      { periodo: "C1 2024" },
      { periodo: "C2 2024" },
    ];
    const sorted = sortByPeriodo(items);
    expect(sorted.map((r) => r.periodo)).toEqual([
      "C1 2024",
      "C2 2024",
      "garbage",
    ]);
  });

  it("uses custom key", () => {
    const items = [
      { period: "C3 2024", x: 1 },
      { period: "C1 2024", x: 2 },
    ];
    const sorted = sortByPeriodo(items, "period");
    expect(sorted.map((r) => r.period)).toEqual(["C1 2024", "C3 2024"]);
  });

  it("preserves extra fields", () => {
    const items = [
      { periodo: "C2 2024", promedio: 85.5 },
      { periodo: "C1 2024", promedio: 90.0 },
    ];
    const sorted = sortByPeriodo(items);
    expect(sorted[0]).toEqual({ periodo: "C1 2024", promedio: 90.0 });
    expect(sorted[1]).toEqual({ periodo: "C2 2024", promedio: 85.5 });
  });
});
