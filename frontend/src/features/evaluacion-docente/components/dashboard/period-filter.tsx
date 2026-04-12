"use client";

import { useMemo } from "react";
import {
  Building2,
  CalendarDays,
  GraduationCap,
  Layers,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { MODALIDADES } from "@/features/evaluacion-docente/lib/business-rules";
import type { Modalidad, PeriodoOption } from "@/features/evaluacion-docente/types";

const ALL_ESCUELAS = "Todas las escuelas";
const ALL_CURSOS = "Todos los cursos";

interface PeriodFilterProps {
  periodos: PeriodoOption[];
  selectedModalidad: Modalidad | undefined;
  selectedPeriodo: string | undefined;
  escuelas: string[];
  cursos: string[];
  selectedEscuela: string | undefined;
  selectedCurso: string | undefined;
  onModalidadChange: (modalidad: Modalidad | undefined) => void;
  onPeriodoChange: (periodo: string | undefined) => void;
  onEscuelaChange: (escuela: string | undefined) => void;
  onCursoChange: (curso: string | undefined) => void;
}

export function PeriodFilter({
  periodos,
  selectedModalidad,
  selectedPeriodo,
  escuelas,
  cursos,
  selectedEscuela,
  selectedCurso,
  onModalidadChange,
  onPeriodoChange,
  onEscuelaChange,
  onCursoChange,
}: PeriodFilterProps) {
  // Group periods by modalidad and count (modalidad comes from backend)
  const modalidadCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const p of periodos) {
      counts[p.modalidad] = (counts[p.modalidad] ?? 0) + 1;
    }
    return counts;
  }, [periodos]);

  // Filter periods for the selected modalidad (already sorted by backend)
  const filteredPeriodos = useMemo(() => {
    if (!selectedModalidad) return [];
    return periodos
      .filter((p) => p.modalidad === selectedModalidad)
      .map((p) => p.periodo);
  }, [periodos, selectedModalidad]);

  const handleModalidadClick = (m: Modalidad) => {
    if (selectedModalidad === m) {
      onModalidadChange(undefined);
      onPeriodoChange(undefined);
    } else {
      onModalidadChange(m);
      onPeriodoChange(undefined);
    }
  };

  const handlePeriodoClick = (p: string) => {
    onPeriodoChange(selectedPeriodo === p ? undefined : p);
  };

  const handleClear = () => {
    onModalidadChange(undefined);
    onPeriodoChange(undefined);
    onEscuelaChange(undefined);
    onCursoChange(undefined);
  };

  const hasSelection =
    selectedModalidad || selectedPeriodo || selectedEscuela || selectedCurso;

  if (periodos.length === 0) return null;

  return (
    <div className="space-y-3">
      {/* Modalidad row */}
      <div className="flex flex-wrap items-center gap-2">
        <Layers className="size-4 text-muted-foreground" />
        <span className="text-sm font-medium text-muted-foreground">
          Modalidad:
        </span>
        {MODALIDADES.map((m) => {
          const count = modalidadCounts[m.value] ?? 0;
          if (count === 0) return null;
          return (
            <Button
              key={m.value}
              variant={selectedModalidad === m.value ? "default" : "outline"}
              size="sm"
              onClick={() => handleModalidadClick(m.value)}
              title={m.description}
            >
              {m.label}
              <span className="ml-1.5 text-xs opacity-60">({count})</span>
            </Button>
          );
        })}
        {hasSelection && (
          <Button
            variant="ghost"
            size="icon-xs"
            onClick={handleClear}
            aria-label="Limpiar filtros"
          >
            <X className="size-3.5" />
          </Button>
        )}
      </div>

      {/* Period row — only shown when a modalidad is selected */}
      {selectedModalidad && filteredPeriodos.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 pl-6">
          <CalendarDays className="size-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">Período:</span>
          {filteredPeriodos.map((p) => (
            <Button
              key={p}
              variant={selectedPeriodo === p ? "default" : "outline"}
              size="sm"
              onClick={() => handlePeriodoClick(p)}
            >
              {p}
            </Button>
          ))}
        </div>
      )}

      {/* Escuela / Curso row */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Escuela */}
        <div className="flex items-center gap-1.5">
          <Building2 className="size-4 text-muted-foreground" />
          <Select
            value={selectedEscuela ?? ALL_ESCUELAS}
            onValueChange={(v) =>
              onEscuelaChange(!v || v === ALL_ESCUELAS ? undefined : v)
            }
          >
            <SelectTrigger size="sm" className="min-w-60">
              <SelectValue placeholder="Todas las escuelas" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL_ESCUELAS}>Todas las escuelas</SelectItem>
              {escuelas.map((e) => (
                <SelectItem key={e} value={e}>
                  {e}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Curso */}
        <div className="flex items-center gap-1.5">
          <GraduationCap className="size-4 text-muted-foreground" />
          <Select
            value={selectedCurso ?? ALL_CURSOS}
            onValueChange={(v) =>
              onCursoChange(!v || v === ALL_CURSOS ? undefined : v)
            }
          >
            <SelectTrigger size="sm" className="min-w-70">
              <SelectValue placeholder="Todos los cursos" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL_CURSOS}>Todos los cursos</SelectItem>
              {cursos.map((c) => (
                <SelectItem key={c} value={c}>
                  {c}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
    </div>
  );
}
