"use client";

import { cn } from "@/lib/utils";

const SENTIMENT_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  positivo: { label: "Positivo", color: "text-emerald-700", bg: "bg-emerald-100" },
  neutro: { label: "Neutro", color: "text-slate-700", bg: "bg-slate-100" },
  mixto: { label: "Mixto", color: "text-amber-700", bg: "bg-amber-100" },
  negativo: { label: "Negativo", color: "text-red-700", bg: "bg-red-100" },
};

const TIPO_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  fortaleza: { label: "Fortaleza", color: "text-emerald-700", bg: "bg-emerald-100" },
  mejora: { label: "Mejora", color: "text-amber-700", bg: "bg-amber-100" },
  observacion: { label: "Observación", color: "text-blue-700", bg: "bg-blue-100" },
};

const TEMA_LABELS: Record<string, string> = {
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

export function SentimentBadge({ value }: { value: string | null }) {
  const cfg = SENTIMENT_CONFIG[value ?? ""] ?? {
    label: value ?? "—",
    color: "text-muted-foreground",
    bg: "bg-muted",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
        cfg.bg,
        cfg.color,
      )}
    >
      {cfg.label}
    </span>
  );
}

export function TipoBadge({ value }: { value: string }) {
  const cfg = TIPO_CONFIG[value] ?? {
    label: value,
    color: "text-muted-foreground",
    bg: "bg-muted",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
        cfg.bg,
        cfg.color,
      )}
    >
      {cfg.label}
    </span>
  );
}

export function TemaBadge({ value }: { value: string }) {
  return (
    <span className="inline-flex items-center rounded-full bg-violet-100 px-2 py-0.5 text-xs font-medium text-violet-700">
      {TEMA_LABELS[value] ?? value}
    </span>
  );
}

export function temaLabel(tema: string): string {
  return TEMA_LABELS[tema] ?? tema;
}

export { SENTIMENT_CONFIG, TIPO_CONFIG, TEMA_LABELS };
