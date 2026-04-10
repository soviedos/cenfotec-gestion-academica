"use client";

import { cn } from "@/lib/utils";
import {
  sentimientoBadgeStyle,
  tipoComentarioBadgeStyle,
  temaLabel,
  sentimientoLabel,
  tipoComentarioLabel,
  SENTIMIENTOS,
  TEMAS,
} from "@/lib/business-rules";
import type { Sentimiento, TipoComentario } from "@/types";

export function SentimentBadge({ value }: { value: string | null }) {
  const cfg = value
    ? sentimientoBadgeStyle(value as Sentimiento)
    : { label: "—", color: "text-muted-foreground", bg: "bg-muted" };
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
  const cfg = tipoComentarioBadgeStyle(value as TipoComentario);
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
      {temaLabel(value)}
    </span>
  );
}

export {
  temaLabel,
  sentimientoLabel,
  tipoComentarioLabel,
  SENTIMIENTOS,
  TEMAS,
};
