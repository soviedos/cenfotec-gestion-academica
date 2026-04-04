"use client";

import { CalendarDays, X } from "lucide-react";
import { Button } from "@/components/ui/button";

interface PeriodFilterProps {
  periodos: string[];
  selected: string | undefined;
  onChange: (periodo: string | undefined) => void;
}

export function PeriodFilter({
  periodos,
  selected,
  onChange,
}: PeriodFilterProps) {
  if (periodos.length === 0) return null;

  return (
    <div className="flex flex-wrap items-center gap-2">
      <CalendarDays className="size-4 text-muted-foreground" />
      <span className="text-sm text-muted-foreground">Período:</span>
      {periodos.map((p) => (
        <Button
          key={p}
          variant={selected === p ? "default" : "outline"}
          size="sm"
          onClick={() => onChange(selected === p ? undefined : p)}
        >
          {p}
        </Button>
      ))}
      {selected && (
        <Button
          variant="ghost"
          size="icon-xs"
          onClick={() => onChange(undefined)}
          aria-label="Limpiar filtro"
        >
          <X className="size-3.5" />
        </Button>
      )}
    </div>
  );
}
