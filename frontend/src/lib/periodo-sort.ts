/**
 * Chronological period sorting utilities [BR-AN-40, VZ-20].
 *
 * Parses period strings like "C2 2025", "M10 2024", "MT3 2026"
 * and sorts them by (year ASC, prefix ASC, number ASC).
 *
 * The backend already sorts, but we apply defensive re-sorting
 * on the frontend to guarantee charts always render in correct order.
 */

interface PeriodoSortKey {
  año: number;
  prefijo: string;
  numero: number;
}

const RE_CUATRIMESTRAL = /^C([1-3])\s+(\d{4})$/i;
const RE_MENSUAL = /^(MT?)(\d{1,2})\s+(\d{4})$/i;
const RE_B2B = /^B2B[\s-]/i;
const RE_YEAR_EXTRACT = /\b(20\d{2})\b/;

/** Fallback key that sorts unparseable periods to the end. */
const FALLBACK: PeriodoSortKey = { año: 9999, prefijo: "ZZZ", numero: 0 };

/**
 * Parse a periodo string into a sortable tuple.
 *
 * @example
 * parsePeriodoKey("C2 2025") // { año: 2025, prefijo: "C", numero: 2 }
 * parsePeriodoKey("M10 2024") // { año: 2024, prefijo: "M", numero: 10 }
 */
export function parsePeriodoKey(periodo: string): PeriodoSortKey {
  const s = periodo.trim().toUpperCase();

  // Cuatrimestral: C1–C3
  const mc = RE_CUATRIMESTRAL.exec(s);
  if (mc) {
    return { año: Number(mc[2]), prefijo: "C", numero: Number(mc[1]) };
  }

  // Mensual: M1–M10, MT1–MT10
  const mm = RE_MENSUAL.exec(s);
  if (mm) {
    return {
      año: Number(mm[3]),
      prefijo: mm[1].toUpperCase(),
      numero: Number(mm[2]),
    };
  }

  // B2B: best-effort year extraction
  if (RE_B2B.test(s)) {
    const my = RE_YEAR_EXTRACT.exec(s);
    return { año: my ? Number(my[1]) : 9999, prefijo: "B2B", numero: 0 };
  }

  return FALLBACK;
}

/**
 * Compare two periodo strings chronologically.
 *
 * Usage: `periodos.sort(comparePeriodos)`
 */
export function comparePeriodos(a: string, b: string): number {
  const ka = parsePeriodoKey(a);
  const kb = parsePeriodoKey(b);

  if (ka.año !== kb.año) return ka.año - kb.año;
  if (ka.prefijo !== kb.prefijo) return ka.prefijo < kb.prefijo ? -1 : 1;
  return ka.numero - kb.numero;
}

/**
 * Sort an array of objects by their periodo field chronologically.
 *
 * @example
 * sortByPeriodo(data, "periodo")
 * // [{ periodo: "C1 2024" }, { periodo: "C3 2024" }, { periodo: "C2 2025" }]
 */
export function sortByPeriodo<T>(
  items: T[],
  key: keyof T = "periodo" as keyof T,
): T[] {
  return [...items].sort((a, b) =>
    comparePeriodos(String(a[key]), String(b[key])),
  );
}
