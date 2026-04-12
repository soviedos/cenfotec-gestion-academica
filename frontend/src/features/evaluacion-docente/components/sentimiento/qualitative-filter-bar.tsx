"use client";

import {
  Building2,
  CalendarDays,
  Filter,
  GraduationCap,
  SlidersHorizontal,
  User,
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
import {
  TEMAS,
  temaLabel,
  SENTIMIENTOS,
  sentimientoLabel,
  TIPOS_COMENTARIO,
  tipoComentarioLabel,
} from "@/features/evaluacion-docente/lib/business-rules";
import type { Sentimiento, Tema, TipoComentario } from "@/features/evaluacion-docente/types";

interface QualitativeFilterBarProps {
  periodo: string | undefined;
  docente: string | undefined;
  asignatura: string | undefined;
  escuela: string | undefined;
  tipo: string | undefined;
  tema: string | undefined;
  sentimiento: string | undefined;
  periodos: string[];
  docentes: string[];
  asignaturas: string[];
  escuelas: string[];
  onPeriodoChange: (v: string | undefined) => void;
  onDocenteChange: (v: string | undefined) => void;
  onAsignaturaChange: (v: string | undefined) => void;
  onEscuelaChange: (v: string | undefined) => void;
  onTipoChange: (v: string | undefined) => void;
  onTemaChange: (v: string | undefined) => void;
  onSentimientoChange: (v: string | undefined) => void;
  onClear: () => void;
}

const TIPOS = TIPOS_COMENTARIO.map((t) => ({
  value: t,
  label: tipoComentarioLabel(t),
}));

const SENTIMIENTO_OPTIONS = SENTIMIENTOS.map((s) => ({
  value: s,
  label: sentimientoLabel(s),
}));

const TEMA_OPTIONS = TEMAS.map((t) => ({
  value: t,
  label: temaLabel(t),
}));

const ALL_ESCUELAS = "Todas las escuelas";
const ALL_PERIODOS = "Todos los períodos";
const ALL_DOCENTES = "Todos los docentes";
const ALL_ASIGNATURAS = "Todas las asignaturas";

export function QualitativeFilterBar({
  periodo,
  docente,
  asignatura,
  escuela,
  tipo,
  tema,
  sentimiento,
  periodos,
  docentes,
  asignaturas,
  escuelas,
  onPeriodoChange,
  onDocenteChange,
  onAsignaturaChange,
  onEscuelaChange,
  onTipoChange,
  onTemaChange,
  onSentimientoChange,
  onClear,
}: QualitativeFilterBarProps) {
  const hasFilters =
    periodo || docente || asignatura || escuela || tipo || tema || sentimiento;

  const activeCount = [
    periodo,
    docente,
    asignatura,
    escuela,
    tipo,
    tema,
    sentimiento,
  ].filter(Boolean).length;

  return (
    <div className="rounded-xl border bg-card p-4 shadow-sm">
      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="size-5 text-primary" />
          <div>
            <h3 className="text-sm font-semibold">Filtros de análisis</h3>
            <p className="text-xs text-muted-foreground">
              Seleccione los criterios para refinar los resultados
              {activeCount > 0 && (
                <span className="ml-1 font-medium text-primary">
                  · {activeCount} filtro{activeCount > 1 ? "s" : ""} activo
                  {activeCount > 1 ? "s" : ""}
                </span>
              )}
            </p>
          </div>
        </div>
        <Button
          variant={hasFilters ? "destructive" : "outline"}
          size="sm"
          onClick={onClear}
          disabled={!hasFilters}
        >
          <X className="mr-1 size-3.5" />
          Limpiar filtros
        </Button>
      </div>

      <div className="space-y-3">
        {/* Dropdown filters row */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Escuela */}
          <div className="flex items-center gap-1.5">
            <Building2 className="size-4 text-muted-foreground" />
            <Select
              value={escuela ?? ALL_ESCUELAS}
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

          {/* Período */}
          <div className="flex items-center gap-1.5">
            <CalendarDays className="size-4 text-muted-foreground" />
            <Select
              value={periodo ?? ALL_PERIODOS}
              onValueChange={(v) =>
                onPeriodoChange(!v || v === ALL_PERIODOS ? undefined : v)
              }
            >
              <SelectTrigger size="sm" className="min-w-40">
                <SelectValue placeholder="Todos los períodos" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL_PERIODOS}>Todos los períodos</SelectItem>
                {periodos.map((p) => (
                  <SelectItem key={p} value={p}>
                    {p}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Docente */}
          <div className="flex items-center gap-1.5">
            <User className="size-4 text-muted-foreground" />
            <Select
              value={docente ?? ALL_DOCENTES}
              onValueChange={(v) =>
                onDocenteChange(!v || v === ALL_DOCENTES ? undefined : v)
              }
            >
              <SelectTrigger size="sm" className="min-w-91">
                <SelectValue placeholder="Todos los docentes" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL_DOCENTES}>Todos los docentes</SelectItem>
                {docentes.map((d) => (
                  <SelectItem key={d} value={d}>
                    {d}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Asignatura */}
          <div className="flex items-center gap-1.5">
            <GraduationCap className="size-4 text-muted-foreground" />
            <Select
              value={asignatura ?? ALL_ASIGNATURAS}
              onValueChange={(v) =>
                onAsignaturaChange(!v || v === ALL_ASIGNATURAS ? undefined : v)
              }
            >
              <SelectTrigger size="sm" className="min-w-83">
                <SelectValue placeholder="Todas las asignaturas" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL_ASIGNATURAS}>
                  Todas las asignaturas
                </SelectItem>
                {asignaturas.map((a) => (
                  <SelectItem key={a} value={a}>
                    {a}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Tipo */}
        <div className="flex flex-wrap items-center gap-2">
          <Filter className="size-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">Tipo:</span>
          {TIPOS.map((t) => (
            <Button
              key={t.value}
              variant={tipo === t.value ? "default" : "outline"}
              size="sm"
              onClick={() =>
                onTipoChange(tipo === t.value ? undefined : t.value)
              }
            >
              {t.label}
            </Button>
          ))}
        </div>

        {/* Sentimiento */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="ml-6 text-sm text-muted-foreground">
            Sentimiento:
          </span>
          {SENTIMIENTO_OPTIONS.map((s) => (
            <Button
              key={s.value}
              variant={sentimiento === s.value ? "default" : "outline"}
              size="sm"
              onClick={() =>
                onSentimientoChange(
                  sentimiento === s.value ? undefined : s.value,
                )
              }
            >
              {s.label}
            </Button>
          ))}
        </div>

        {/* Tema */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="ml-6 text-sm text-muted-foreground">Tema:</span>
          {TEMA_OPTIONS.map((t) => (
            <Button
              key={t.value}
              variant={tema === t.value ? "default" : "outline"}
              size="sm"
              onClick={() =>
                onTemaChange(tema === t.value ? undefined : t.value)
              }
            >
              {t.label}
            </Button>
          ))}
        </div>
      </div>
    </div>
  );
}
