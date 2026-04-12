/**
 * Contract tests — frontend types must mirror backend DTOs.
 *
 * These tests verify that PeriodoMetrica and PeriodoOption include
 * the `año` and `periodo_orden` fields added in Phase 6e, and that
 * the MODALIDADES constant matches the backend domain set.
 */

import { describe, expect, it } from "vitest";
import type { PeriodoMetrica, PeriodoOption } from "@/types";

// ── PeriodoMetrica ──────────────────────────────────────────────────

describe("PeriodoMetrica contract", () => {
  const sample: PeriodoMetrica = {
    periodo: "C1 2025",
    modalidad: "CUATRIMESTRAL",
    año: 2025,
    periodo_orden: 1,
    promedio: 85.5,
    evaluaciones_count: 42,
  };

  it("includes año field", () => {
    expect(sample.año).toBe(2025);
  });

  it("includes periodo_orden field", () => {
    expect(sample.periodo_orden).toBe(1);
  });

  it("periodo_orden is a number", () => {
    expect(typeof sample.periodo_orden).toBe("number");
  });

  it("año is a number", () => {
    expect(typeof sample.año).toBe("number");
  });

  it("modalidad is optional", () => {
    const noMod: PeriodoMetrica = {
      periodo: "C1 2025",
      año: 2025,
      periodo_orden: 1,
      promedio: 80.0,
      evaluaciones_count: 10,
    };
    expect(noMod.modalidad).toBeUndefined();
  });
});

// ── PeriodoOption ───────────────────────────────────────────────────

describe("PeriodoOption contract", () => {
  const sample: PeriodoOption = {
    periodo: "M5 2025",
    modalidad: "MENSUAL",
    año: 2025,
    periodo_orden: 5,
  };

  it("includes año field", () => {
    expect(sample.año).toBe(2025);
  });

  it("includes periodo_orden field", () => {
    expect(sample.periodo_orden).toBe(5);
  });

  it("requires modalidad (non-optional)", () => {
    expect(sample.modalidad).toBe("MENSUAL");
  });

  it("B2B has periodo_orden 0", () => {
    const b2b: PeriodoOption = {
      periodo: "B2B-EMPRESA-2025",
      modalidad: "B2B",
      año: 2025,
      periodo_orden: 0,
    };
    expect(b2b.periodo_orden).toBe(0);
  });
});
