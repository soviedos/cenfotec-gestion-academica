/**
 * Business-rules constants and helpers for the frontend.
 *
 * Single source of truth for labels, colors, validation and display
 * utilities that mirror the backend domain enums and rules defined in
 * docs/business-rules/evaluation-rules.md.
 *
 * Re-exports periodo-sort utilities for convenience.
 */

import type {
  AlertaEstado,
  Modalidad,
  ModalidadConDesconocida,
  Sentimiento,
  Severidad,
  Tema,
  TipoAlerta,
  TipoComentario,
} from "@/types";

// Re-export periodo sorting so consumers can import everything from one place
export {
  comparePeriodos,
  parsePeriodoKey,
  sortByPeriodo,
} from "./periodo-sort";

// ════════════════════════════════════════════════════════════════════════
//  Modalidad [BR-MOD-01, BR-FE-01, BR-FE-02]
// ════════════════════════════════════════════════════════════════════════

export interface ModalidadOption {
  value: Modalidad;
  label: string;
  description: string;
}

/** Ordered list of selectable modalidades [BR-FE-02]. */
export const MODALIDADES: readonly ModalidadOption[] = [
  {
    value: "CUATRIMESTRAL",
    label: "Cuatrimestral",
    description: "C1–C3 (3 periodos por año)",
  },
  {
    value: "MENSUAL",
    label: "Mensual",
    description: "M1–M10, MT1–MT10",
  },
  {
    value: "B2B",
    label: "B2B",
    description: "Programas corporativos",
  },
] as const;

const MODALIDAD_LABELS: Record<ModalidadConDesconocida, string> = {
  CUATRIMESTRAL: "Cuatrimestral",
  MENSUAL: "Mensual",
  B2B: "B2B",
  DESCONOCIDA: "Desconocida",
};

/** Friendly display label for a modalidad value. */
export function modalidadLabel(m: ModalidadConDesconocida): string {
  return MODALIDAD_LABELS[m] ?? m;
}

/** Whether a string is a valid Modalidad (excluding DESCONOCIDA). */
export function isModalidad(v: string): v is Modalidad {
  return v === "CUATRIMESTRAL" || v === "MENSUAL" || v === "B2B";
}

// ════════════════════════════════════════════════════════════════════════
//  Periodo validation [BR-MOD-03, BR-AN-41]
// ════════════════════════════════════════════════════════════════════════

const RE_CUATRIMESTRAL = /^C[1-3]\s+\d{4}$/i;
const RE_MENSUAL = /^MT?\d{1,2}\s+\d{4}$/i;
const RE_B2B = /^B2B[\s-].+/i;

/** Check if a periodo string matches any known format [BR-MOD-03]. */
export function isValidPeriodo(periodo: string): boolean {
  const s = periodo.trim();
  return RE_CUATRIMESTRAL.test(s) || RE_MENSUAL.test(s) || RE_B2B.test(s);
}

/** Infer the modalidad from a raw periodo string [BR-MOD-03]. */
export function modalidadFromPeriodo(periodo: string): ModalidadConDesconocida {
  const s = periodo.trim().toUpperCase();
  if (s.startsWith("B2B")) return "B2B";
  if (RE_CUATRIMESTRAL.test(s)) return "CUATRIMESTRAL";
  if (RE_MENSUAL.test(s)) return "MENSUAL";
  return "DESCONOCIDA";
}

// ════════════════════════════════════════════════════════════════════════
//  Severidad [AL-20, VZ-51, BR-FE-21]
// ════════════════════════════════════════════════════════════════════════

export const SEVERIDADES: readonly Severidad[] = ["alta", "media", "baja"];

const SEVERIDAD_LABELS: Record<Severidad, string> = {
  alta: "Alta",
  media: "Media",
  baja: "Baja",
};

/** Friendly label. */
export function severidadLabel(s: Severidad): string {
  return SEVERIDAD_LABELS[s] ?? s;
}

/**
 * Tailwind classes for alert severity styling [VZ-51, BR-FE-21].
 *
 * Returns bg + text + border classes suitable for cards/badges.
 */
const SEVERIDAD_STYLES: Record<Severidad, string> = {
  alta: "bg-red-500/10 text-red-600 border-red-500/20",
  media: "bg-amber-500/10 text-amber-600 border-amber-500/20",
  baja: "bg-muted text-muted-foreground border-border",
};

export function severidadClasses(s: Severidad): string {
  return SEVERIDAD_STYLES[s] ?? "";
}

/**
 * Badge variant name for Shadcn Badge component [BR-FE-21].
 */
const SEVERIDAD_BADGE_VARIANT: Record<Severidad, string> = {
  alta: "destructive",
  media: "warning",
  baja: "secondary",
};

export function severidadBadgeVariant(s: Severidad): string {
  return SEVERIDAD_BADGE_VARIANT[s] ?? "secondary";
}

/**
 * Sort comparator: alta < media < baja (most severe first) [BR-FE-20].
 */
const SEVERIDAD_ORDER: Record<Severidad, number> = {
  alta: 0,
  media: 1,
  baja: 2,
};

export function compareSeveridad(a: Severidad, b: Severidad): number {
  return (SEVERIDAD_ORDER[a] ?? 3) - (SEVERIDAD_ORDER[b] ?? 3);
}

// ════════════════════════════════════════════════════════════════════════
//  Alert thresholds [AL-20, AL-21]
//
//  Authoritative source: backend/app/domain/alert_rules.py
//  Runtime endpoint:     GET /api/v1/config/alert-thresholds
//
//  These constants are kept as static defaults for immediate rendering.
//  If dynamic thresholds are needed, fetch from the config endpoint
//  and override at runtime.
// ════════════════════════════════════════════════════════════════════════

/** Absolute performance thresholds [AL-20]. */
export const ALERT_THRESHOLDS = {
  HIGH: 60.0,
  MEDIUM: 70.0,
  LOW: 80.0,
} as const;

/** Drop between consecutive periods [AL-21]. */
export const DROP_THRESHOLDS = {
  HIGH: 15.0,
  MEDIUM: 10.0,
  LOW: 5.0,
} as const;

// ════════════════════════════════════════════════════════════════════════
//  Tipo de alerta [AL-20–AL-23]
// ════════════════════════════════════════════════════════════════════════

const TIPO_ALERTA_LABELS: Record<TipoAlerta, string> = {
  BAJO_DESEMPEÑO: "Bajo desempeño",
  CAIDA: "Caída",
  SENTIMIENTO: "Sentimiento",
  PATRON: "Patrón",
};

export function tipoAlertaLabel(t: TipoAlerta): string {
  return TIPO_ALERTA_LABELS[t] ?? t;
}

// ════════════════════════════════════════════════════════════════════════
//  Alerta estado [AL-50]
// ════════════════════════════════════════════════════════════════════════

const ALERTA_ESTADO_LABELS: Record<AlertaEstado, string> = {
  activa: "Activa",
  revisada: "Revisada",
  resuelta: "Resuelta",
  descartada: "Descartada",
};

export function alertaEstadoLabel(e: AlertaEstado): string {
  return ALERTA_ESTADO_LABELS[e] ?? e;
}

// ════════════════════════════════════════════════════════════════════════
//  Sentimiento [VZ-50]
// ════════════════════════════════════════════════════════════════════════

export const SENTIMIENTOS: readonly Sentimiento[] = [
  "positivo",
  "negativo",
  "mixto",
  "neutro",
];

const SENTIMIENTO_LABELS: Record<Sentimiento, string> = {
  positivo: "Positivo",
  negativo: "Negativo",
  mixto: "Mixto",
  neutro: "Neutro",
};

export function sentimientoLabel(s: Sentimiento): string {
  return SENTIMIENTO_LABELS[s] ?? s;
}

/**
 * Standard sentiment hex colors [VZ-50].
 *
 * For chart fills / Recharts – use hex values directly.
 */
const SENTIMIENTO_HEX: Record<Sentimiento, string> = {
  positivo: "#22c55e",
  negativo: "#ef4444",
  mixto: "#f59e0b",
  neutro: "#94a3b8",
};

export function sentimientoColor(s: Sentimiento): string {
  return SENTIMIENTO_HEX[s] ?? "#94a3b8";
}

/**
 * Tailwind text-color classes for sentiment labels.
 */
const SENTIMIENTO_TEXT_CLASSES: Record<Sentimiento, string> = {
  positivo: "text-green-500",
  negativo: "text-red-500",
  mixto: "text-amber-500",
  neutro: "text-muted-foreground",
};

export function sentimientoTextClass(s: Sentimiento): string {
  return SENTIMIENTO_TEXT_CLASSES[s] ?? "text-muted-foreground";
}

// ════════════════════════════════════════════════════════════════════════
//  Tema [BR-CLAS-10]
// ════════════════════════════════════════════════════════════════════════

export const TEMAS: readonly Tema[] = [
  "metodologia",
  "dominio_tema",
  "comunicacion",
  "evaluacion",
  "puntualidad",
  "material",
  "actitud",
  "tecnologia",
  "organizacion",
  "otro",
];

const TEMA_LABELS: Record<Tema, string> = {
  metodologia: "Metodología",
  dominio_tema: "Dominio del tema",
  comunicacion: "Comunicación",
  evaluacion: "Evaluación",
  puntualidad: "Puntualidad",
  material: "Material",
  actitud: "Actitud",
  tecnologia: "Tecnología",
  organizacion: "Organización",
  otro: "Otro",
};

export function temaLabel(t: Tema): string {
  return TEMA_LABELS[t] ?? t;
}

// ════════════════════════════════════════════════════════════════════════
//  Tipo de comentario [BR-CLAS-01]
// ════════════════════════════════════════════════════════════════════════

const TIPO_COMENTARIO_LABELS: Record<TipoComentario, string> = {
  fortaleza: "Fortaleza",
  mejora: "Mejora",
  observacion: "Observación",
};

export function tipoComentarioLabel(t: TipoComentario): string {
  return TIPO_COMENTARIO_LABELS[t] ?? t;
}
