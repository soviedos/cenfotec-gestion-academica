import { describe, expect, it } from "vitest";
import {
  ALERT_THRESHOLDS,
  compareSeveridad,
  DROP_THRESHOLDS,
  isModalidad,
  isValidPeriodo,
  MODALIDADES,
  modalidadFromPeriodo,
  modalidadLabel,
  SENTIMIENTOS,
  sentimientoColor,
  sentimientoLabel,
  sentimientoTextClass,
  severidadBadgeVariant,
  severidadClasses,
  severidadLabel,
  SEVERIDADES,
  TEMAS,
  temaLabel,
  tipoAlertaLabel,
  tipoComentarioLabel,
  alertaEstadoLabel,
} from "@/lib/business-rules";

// ════════════════════════════════════════════════════════════════
//  Modalidad
// ════════════════════════════════════════════════════════════════

describe("Modalidad helpers", () => {
  it("MODALIDADES has 3 options", () => {
    expect(MODALIDADES).toHaveLength(3);
    expect(MODALIDADES.map((m) => m.value)).toEqual([
      "CUATRIMESTRAL",
      "MENSUAL",
      "B2B",
    ]);
  });

  it("modalidadLabel returns friendly labels", () => {
    expect(modalidadLabel("CUATRIMESTRAL")).toBe("Cuatrimestral");
    expect(modalidadLabel("MENSUAL")).toBe("Mensual");
    expect(modalidadLabel("B2B")).toBe("B2B");
    expect(modalidadLabel("DESCONOCIDA")).toBe("Desconocida");
  });

  it("isModalidad validates known values", () => {
    expect(isModalidad("CUATRIMESTRAL")).toBe(true);
    expect(isModalidad("MENSUAL")).toBe(true);
    expect(isModalidad("B2B")).toBe(true);
    expect(isModalidad("DESCONOCIDA")).toBe(false);
    expect(isModalidad("garbage")).toBe(false);
  });
});

// ════════════════════════════════════════════════════════════════
//  Periodo validation
// ════════════════════════════════════════════════════════════════

describe("Periodo validation", () => {
  it.each([
    "C1 2025",
    "C3 2024",
    "M1 2026",
    "M10 2025",
    "MT3 2024",
    "B2B-EMPRESA-2025",
    "B2B Microsoft 2026",
  ])("isValidPeriodo('%s') is true", (p) => {
    expect(isValidPeriodo(p)).toBe(true);
  });

  it.each(["garbage", "", "X1 2025", "C4 2025", "2025"])(
    "isValidPeriodo('%s') is false",
    (p) => {
      expect(isValidPeriodo(p)).toBe(false);
    },
  );

  it("modalidadFromPeriodo infers cuatrimestral", () => {
    expect(modalidadFromPeriodo("C2 2025")).toBe("CUATRIMESTRAL");
  });

  it("modalidadFromPeriodo infers mensual", () => {
    expect(modalidadFromPeriodo("M10 2024")).toBe("MENSUAL");
    expect(modalidadFromPeriodo("MT3 2026")).toBe("MENSUAL");
  });

  it("modalidadFromPeriodo infers B2B", () => {
    expect(modalidadFromPeriodo("B2B-EMPRESA-2025")).toBe("B2B");
  });

  it("modalidadFromPeriodo returns DESCONOCIDA for unknown", () => {
    expect(modalidadFromPeriodo("garbage")).toBe("DESCONOCIDA");
  });
});

// ════════════════════════════════════════════════════════════════
//  Severidad
// ════════════════════════════════════════════════════════════════

describe("Severidad helpers", () => {
  it("SEVERIDADES has correct order", () => {
    expect(SEVERIDADES).toEqual(["alta", "media", "baja"]);
  });

  it("severidadLabel returns friendly labels", () => {
    expect(severidadLabel("alta")).toBe("Alta");
    expect(severidadLabel("media")).toBe("Media");
    expect(severidadLabel("baja")).toBe("Baja");
  });

  it("severidadClasses returns Tailwind classes [VZ-51]", () => {
    expect(severidadClasses("alta")).toContain("red");
    expect(severidadClasses("media")).toContain("amber");
    expect(severidadClasses("baja")).toContain("muted");
  });

  it("severidadBadgeVariant maps to Shadcn variants [BR-FE-21]", () => {
    expect(severidadBadgeVariant("alta")).toBe("destructive");
    expect(severidadBadgeVariant("media")).toBe("warning");
    expect(severidadBadgeVariant("baja")).toBe("secondary");
  });

  it("compareSeveridad sorts alta first [BR-FE-20]", () => {
    const severities = ["baja", "alta", "media"] as const;
    const sorted = [...severities].sort(compareSeveridad);
    expect(sorted).toEqual(["alta", "media", "baja"]);
  });
});

// ════════════════════════════════════════════════════════════════
//  Alert thresholds
// ════════════════════════════════════════════════════════════════

describe("Alert thresholds [AL-20, AL-21]", () => {
  it("absolute thresholds descend", () => {
    expect(ALERT_THRESHOLDS.HIGH).toBeLessThan(ALERT_THRESHOLDS.MEDIUM);
    expect(ALERT_THRESHOLDS.MEDIUM).toBeLessThan(ALERT_THRESHOLDS.LOW);
  });

  it("drop thresholds descend", () => {
    expect(DROP_THRESHOLDS.HIGH).toBeGreaterThan(DROP_THRESHOLDS.MEDIUM);
    expect(DROP_THRESHOLDS.MEDIUM).toBeGreaterThan(DROP_THRESHOLDS.LOW);
  });

  it("matches backend constants", () => {
    expect(ALERT_THRESHOLDS.HIGH).toBe(60.0);
    expect(ALERT_THRESHOLDS.MEDIUM).toBe(70.0);
    expect(ALERT_THRESHOLDS.LOW).toBe(80.0);
    expect(DROP_THRESHOLDS.HIGH).toBe(15.0);
    expect(DROP_THRESHOLDS.MEDIUM).toBe(10.0);
    expect(DROP_THRESHOLDS.LOW).toBe(5.0);
  });
});

// ════════════════════════════════════════════════════════════════
//  Tipo de alerta
// ════════════════════════════════════════════════════════════════

describe("Tipo alerta labels", () => {
  it("returns friendly labels for all types", () => {
    expect(tipoAlertaLabel("BAJO_DESEMPEÑO")).toBe("Bajo desempeño");
    expect(tipoAlertaLabel("CAIDA")).toBe("Caída");
    expect(tipoAlertaLabel("SENTIMIENTO")).toBe("Sentimiento");
    expect(tipoAlertaLabel("PATRON")).toBe("Patrón");
  });
});

// ════════════════════════════════════════════════════════════════
//  Alerta estado
// ════════════════════════════════════════════════════════════════

describe("Alerta estado labels", () => {
  it("returns labels for all states", () => {
    expect(alertaEstadoLabel("activa")).toBe("Activa");
    expect(alertaEstadoLabel("revisada")).toBe("Revisada");
    expect(alertaEstadoLabel("resuelta")).toBe("Resuelta");
    expect(alertaEstadoLabel("descartada")).toBe("Descartada");
  });
});

// ════════════════════════════════════════════════════════════════
//  Sentimiento
// ════════════════════════════════════════════════════════════════

describe("Sentimiento helpers [VZ-50]", () => {
  it("SENTIMIENTOS has all 4 values", () => {
    expect(SENTIMIENTOS).toHaveLength(4);
  });

  it("sentimientoLabel provides Spanish labels", () => {
    expect(sentimientoLabel("positivo")).toBe("Positivo");
    expect(sentimientoLabel("negativo")).toBe("Negativo");
    expect(sentimientoLabel("mixto")).toBe("Mixto");
    expect(sentimientoLabel("neutro")).toBe("Neutro");
  });

  it("sentimientoColor returns hex per VZ-50", () => {
    expect(sentimientoColor("positivo")).toBe("#22c55e");
    expect(sentimientoColor("negativo")).toBe("#ef4444");
    expect(sentimientoColor("mixto")).toBe("#f59e0b");
    expect(sentimientoColor("neutro")).toBe("#94a3b8");
  });

  it("sentimientoTextClass returns Tailwind class", () => {
    expect(sentimientoTextClass("positivo")).toContain("green");
    expect(sentimientoTextClass("negativo")).toContain("red");
    expect(sentimientoTextClass("mixto")).toContain("amber");
    expect(sentimientoTextClass("neutro")).toContain("muted");
  });
});

// ════════════════════════════════════════════════════════════════
//  Tema
// ════════════════════════════════════════════════════════════════

describe("Tema helpers [BR-CLAS-10]", () => {
  it("TEMAS has all 10 values", () => {
    expect(TEMAS).toHaveLength(10);
  });

  it("temaLabel returns friendly labels", () => {
    expect(temaLabel("metodologia")).toBe("Metodología");
    expect(temaLabel("dominio_tema")).toBe("Dominio del tema");
    expect(temaLabel("comunicacion")).toBe("Comunicación");
    expect(temaLabel("otro")).toBe("Otro");
  });
});

// ════════════════════════════════════════════════════════════════
//  Tipo de comentario
// ════════════════════════════════════════════════════════════════

describe("Tipo comentario labels [BR-CLAS-01]", () => {
  it("returns labels for all types", () => {
    expect(tipoComentarioLabel("fortaleza")).toBe("Fortaleza");
    expect(tipoComentarioLabel("mejora")).toBe("Mejora");
    expect(tipoComentarioLabel("observacion")).toBe("Observación");
  });
});
