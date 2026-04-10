import { describe, expect, it } from "vitest";
import {
  compareSeveridad,
  MODALIDADES,
  modalidadLabel,
  SENTIMIENTOS,
  sentimientoColor,
  sentimientoLabel,
  sentimientoTextClass,
  sentimientoBadgeStyle,
  severidadBadgeVariant,
  severidadClasses,
  severidadLabel,
  SEVERIDADES,
  TEMAS,
  temaLabel,
  tipoAlertaLabel,
  tipoComentarioLabel,
  tipoComentarioBadgeStyle,
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
});

// Period validation and modalidad inference are now handled
// exclusively by the backend (see backend/app/domain/periodo.py).

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

// Alert thresholds are backend-only (backend/app/domain/alert_rules.py).
// No frontend constants to test.

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

// ════════════════════════════════════════════════════════════════
//  Badge styles
// ════════════════════════════════════════════════════════════════

describe("Badge style helpers", () => {
  it("sentimientoBadgeStyle returns label and classes", () => {
    const style = sentimientoBadgeStyle("positivo");
    expect(style.label).toBe("Positivo");
    expect(style.color).toContain("emerald");
    expect(style.bg).toContain("emerald");
  });

  it("tipoComentarioBadgeStyle returns label and classes", () => {
    const style = tipoComentarioBadgeStyle("fortaleza");
    expect(style.label).toBe("Fortaleza");
    expect(style.color).toContain("emerald");
  });
});
