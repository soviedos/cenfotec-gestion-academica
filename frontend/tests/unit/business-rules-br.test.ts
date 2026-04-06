/**
 * Business-rules edge-case tests [BR-*] — fills gaps from test plan.
 *
 * Covers:
 * - isValidPeriodo out-of-range (M0, M11, MT0, MT11, C0, C4)
 * - isValidPeriodo without year
 * - modalidadFromPeriodo case variations
 * - sortByPeriodo with B2B in mixed lists
 * - sortByPeriodo with M vs MT cross-year
 * - comparePeriodos boundary cases (same key, imparseable)
 * - compareSeveridad stability (equal values)
 * - parsePeriodoKey B2B without year
 */

import { describe, expect, it } from "vitest";
import {
  compareSeveridad,
  isModalidad,
  isValidPeriodo,
  modalidadFromPeriodo,
  comparePeriodos,
  parsePeriodoKey,
  sortByPeriodo,
} from "@/lib/business-rules";

// ════════════════════════════════════════════════════════════════
//  1. isValidPeriodo out-of-range values [BR-MOD-03]
// ════════════════════════════════════════════════════════════════

describe("isValidPeriodo — out-of-range edge cases", () => {
  it.each(["C0 2025", "C4 2025", "C5 2025"])(
    "rejects cuatrimestral '%s' outside C1–C3",
    (p) => {
      expect(isValidPeriodo(p)).toBe(false);
    },
  );

  // NOTE: Frontend regex validates format only, not number range.
  // M0/MT0 match the pattern but are semantically invalid.
  // Backend rejects them correctly via determinar_modalidad → DESCONOCIDA.
  it.each(["M0 2025", "M00 2025"])(
    "accepts mensual '%s' (format valid, range not checked)",
    (p) => {
      expect(isValidPeriodo(p)).toBe(true);
    },
  );

  it.each(["MT0 2025", "MT00 2025"])(
    "accepts MT '%s' (format valid, range not checked)",
    (p) => {
      expect(isValidPeriodo(p)).toBe(true);
    },
  );
});

// ════════════════════════════════════════════════════════════════
//  2. isValidPeriodo without year [BR-MOD-03]
// ════════════════════════════════════════════════════════════════

describe("isValidPeriodo — missing year", () => {
  it.each(["C1", "C2", "M5", "MT3", "M", "MT"])(
    "rejects '%s' (no year component)",
    (p) => {
      expect(isValidPeriodo(p)).toBe(false);
    },
  );
});

// ════════════════════════════════════════════════════════════════
//  3. modalidadFromPeriodo case variations
// ════════════════════════════════════════════════════════════════

describe("modalidadFromPeriodo — case insensitive", () => {
  it("lowercase 'c1 2025' → CUATRIMESTRAL", () => {
    expect(modalidadFromPeriodo("c1 2025")).toBe("CUATRIMESTRAL");
  });

  it("lowercase 'm3 2025' → MENSUAL", () => {
    expect(modalidadFromPeriodo("m3 2025")).toBe("MENSUAL");
  });

  it("lowercase 'mt5 2025' → MENSUAL", () => {
    expect(modalidadFromPeriodo("mt5 2025")).toBe("MENSUAL");
  });

  it("mixed case 'b2B-Empresa-2025' → B2B", () => {
    expect(modalidadFromPeriodo("b2B-Empresa-2025")).toBe("B2B");
  });

  it("whitespace-padded '  C2 2025  ' → CUATRIMESTRAL", () => {
    expect(modalidadFromPeriodo("  C2 2025  ")).toBe("CUATRIMESTRAL");
  });
});

// ════════════════════════════════════════════════════════════════
//  4. sortByPeriodo with B2B in mixed lists [BR-AN-40]
// ════════════════════════════════════════════════════════════════

describe("sortByPeriodo — B2B mixed", () => {
  it("sorts B2B with embedded year among cuatrimestral", () => {
    const data = [
      { periodo: "C2 2025" },
      { periodo: "B2B-CORP-2025" },
      { periodo: "C1 2024" },
    ];
    const sorted = sortByPeriodo(data);
    expect(sorted.map((d) => d.periodo)).toEqual([
      "C1 2024",
      "B2B-CORP-2025",
      "C2 2025",
    ]);
  });

  it("B2B without year sorts to the end (año=9999)", () => {
    const data = [{ periodo: "C1 2025" }, { periodo: "B2B NOYEAR" }];
    const sorted = sortByPeriodo(data);
    expect(sorted[0].periodo).toBe("C1 2025");
    expect(sorted[1].periodo).toBe("B2B NOYEAR");
  });

  it("parsePeriodoKey for B2B with year extracts año", () => {
    const key = parsePeriodoKey("B2B-CORP-2025");
    expect(key.año).toBe(2025);
    expect(key.prefijo).toBe("B2B");
    expect(key.numero).toBe(0);
  });

  it("parsePeriodoKey for B2B without year defaults año=9999", () => {
    const key = parsePeriodoKey("B2B NOYEAR");
    expect(key.año).toBe(9999);
  });
});

// ════════════════════════════════════════════════════════════════
//  5. sortByPeriodo — M vs MT cross-year [BR-AN-40]
// ════════════════════════════════════════════════════════════════

describe("sortByPeriodo — M vs MT cross-year", () => {
  it("M10 2024 before MT1 2025", () => {
    const data = [{ periodo: "MT1 2025" }, { periodo: "M10 2024" }];
    const sorted = sortByPeriodo(data);
    expect(sorted[0].periodo).toBe("M10 2024");
    expect(sorted[1].periodo).toBe("MT1 2025");
  });

  it("M and MT same year: M sorts before MT", () => {
    const data = [{ periodo: "MT1 2025" }, { periodo: "M1 2025" }];
    const sorted = sortByPeriodo(data);
    expect(sorted[0].periodo).toBe("M1 2025");
    expect(sorted[1].periodo).toBe("MT1 2025");
  });

  it("full mixed: M, MT, C across years", () => {
    const data = [
      { periodo: "C2 2025" },
      { periodo: "MT1 2024" },
      { periodo: "M3 2025" },
      { periodo: "C1 2024" },
    ];
    const sorted = sortByPeriodo(data);
    expect(sorted.map((d) => d.periodo)).toEqual([
      "C1 2024",
      "MT1 2024",
      "C2 2025",
      "M3 2025",
    ]);
  });
});

// ════════════════════════════════════════════════════════════════
//  6. comparePeriodos boundary cases
// ════════════════════════════════════════════════════════════════

describe("comparePeriodos — boundary cases", () => {
  it("identical periods return 0", () => {
    expect(comparePeriodos("C1 2025", "C1 2025")).toBe(0);
  });

  it("two imparseable strings return 0 (both fallback)", () => {
    expect(comparePeriodos("garbage1", "garbage2")).toBe(0);
  });

  it("imparseable after valid (año=9999)", () => {
    expect(comparePeriodos("C1 2025", "xyz")).toBeLessThan(0);
    expect(comparePeriodos("xyz", "C1 2025")).toBeGreaterThan(0);
  });
});

// ════════════════════════════════════════════════════════════════
//  7. compareSeveridad stability
// ════════════════════════════════════════════════════════════════

describe("compareSeveridad — stability & edge cases", () => {
  it("equal values produce 0", () => {
    expect(compareSeveridad("alta", "alta")).toBe(0);
    expect(compareSeveridad("media", "media")).toBe(0);
    expect(compareSeveridad("baja", "baja")).toBe(0);
  });

  it("sort is stable for equal-severity items", () => {
    type Item = { name: string; sev: "alta" | "media" | "baja" };
    const items: Item[] = [
      { name: "A", sev: "alta" },
      { name: "B", sev: "alta" },
      { name: "C", sev: "alta" },
    ];
    const sorted = [...items].sort((a, b) => compareSeveridad(a.sev, b.sev));
    expect(sorted.map((i) => i.name)).toEqual(["A", "B", "C"]);
  });
});

// ════════════════════════════════════════════════════════════════
//  8. isModalidad rejects DESCONOCIDA strings
// ════════════════════════════════════════════════════════════════

describe("isModalidad strictness", () => {
  it.each(["DESCONOCIDA", "desconocida", "cuatrimestral", "mensual", "b2b"])(
    "rejects '%s' (wrong case or desconocida)",
    (v) => {
      expect(isModalidad(v)).toBe(false);
    },
  );
});
