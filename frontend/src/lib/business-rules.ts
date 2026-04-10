/**
 * UI display helpers for the frontend.
 *
 * Single source of truth for labels, colors, and display utilities
 * that map backend domain enums to user-facing presentation.
 *
 * All business rules, validation, thresholds, and domain logic live
 * exclusively in the backend. The frontend trusts backend responses
 * and only handles presentation mapping.
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

export function temaLabel(t: string): string {
  return TEMA_LABELS[t as Tema] ?? t;
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

// ════════════════════════════════════════════════════════════════════════
//  Badge styling [BR-FE-21]
//
//  Tailwind classes for badge components. Kept here so every badge
//  across the app uses the same color palette.
// ════════════════════════════════════════════════════════════════════════

export interface BadgeStyle {
  label: string;
  color: string;
  bg: string;
}

const SENTIMIENTO_BADGE_STYLES: Record<Sentimiento, BadgeStyle> = {
  positivo: {
    label: "Positivo",
    color: "text-emerald-700",
    bg: "bg-emerald-100",
  },
  negativo: {
    label: "Negativo",
    color: "text-red-700",
    bg: "bg-red-100",
  },
  mixto: { label: "Mixto", color: "text-amber-700", bg: "bg-amber-100" },
  neutro: { label: "Neutro", color: "text-slate-700", bg: "bg-slate-100" },
};

export function sentimientoBadgeStyle(s: Sentimiento): BadgeStyle {
  return (
    SENTIMIENTO_BADGE_STYLES[s] ?? {
      label: s,
      color: "text-muted-foreground",
      bg: "bg-muted",
    }
  );
}

const TIPO_COMENTARIO_BADGE_STYLES: Record<TipoComentario, BadgeStyle> = {
  fortaleza: {
    label: "Fortaleza",
    color: "text-emerald-700",
    bg: "bg-emerald-100",
  },
  mejora: { label: "Mejora", color: "text-amber-700", bg: "bg-amber-100" },
  observacion: {
    label: "Observación",
    color: "text-blue-700",
    bg: "bg-blue-100",
  },
};

export function tipoComentarioBadgeStyle(t: TipoComentario): BadgeStyle {
  return (
    TIPO_COMENTARIO_BADGE_STYLES[t] ?? {
      label: t,
      color: "text-muted-foreground",
      bg: "bg-muted",
    }
  );
}
