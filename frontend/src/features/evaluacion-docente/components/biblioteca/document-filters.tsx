"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Search, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { listPeriodos } from "@/features/evaluacion-docente/lib/api/documents";
import type { DocumentoEstado } from "@/features/evaluacion-docente/types";

interface DocumentFiltersProps {
  onFilterChange: (filters: FilterValues) => void;
  isLoading?: boolean;
}

export interface FilterValues {
  nombre_archivo?: string;
  docente?: string;
  periodo?: string;
  estado?: DocumentoEstado | "";
}

const DEBOUNCE_MS = 400;

export function DocumentFilters({
  onFilterChange,
  isLoading,
}: DocumentFiltersProps) {
  const [search, setSearch] = useState("");
  const [docente, setDocente] = useState("");
  const [periodo, setPeriodo] = useState("");
  const [estado, setEstado] = useState<DocumentoEstado | "">("");
  const [periodos, setPeriodos] = useState<string[]>([]);
  const debounceTimer = useRef<ReturnType<typeof setTimeout> | undefined>(
    undefined,
  );

  // Fetch available periodos on mount
  useEffect(() => {
    listPeriodos()
      .then(setPeriodos)
      .catch(() => {});
  }, []);

  const hasActiveFilters = search || docente || periodo || estado;

  const emitFilters = useCallback(
    (overrides: Partial<FilterValues> = {}) => {
      const values: FilterValues = {
        nombre_archivo: search,
        docente,
        periodo,
        estado,
        ...overrides,
      };
      onFilterChange(values);
    },
    [search, docente, periodo, estado, onFilterChange],
  );

  // Debounce text inputs
  const handleSearchChange = (value: string) => {
    setSearch(value);
    clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      emitFilters({ nombre_archivo: value });
    }, DEBOUNCE_MS);
  };

  const handleDocenteChange = (value: string) => {
    setDocente(value);
    clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      emitFilters({ docente: value });
    }, DEBOUNCE_MS);
  };

  // Immediate for selects
  const handleEstadoChange = (value: DocumentoEstado | "") => {
    setEstado(value);
    emitFilters({ estado: value });
  };

  const handlePeriodoChange = (value: string) => {
    setPeriodo(value);
    emitFilters({ periodo: value });
  };

  const clearAll = () => {
    setSearch("");
    setDocente("");
    setPeriodo("");
    setEstado("");
    clearTimeout(debounceTimer.current);
    onFilterChange({});
  };

  useEffect(() => {
    return () => clearTimeout(debounceTimer.current);
  }, []);

  return (
    <div
      className="flex flex-col gap-3 sm:flex-row sm:items-center sm:flex-wrap"
      role="search"
      aria-label="Filtros de documentos"
    >
      {/* Search by filename */}
      <div className="relative flex-1 min-w-48">
        <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Buscar por nombre de archivo..."
          value={search}
          onChange={(e) => handleSearchChange(e.target.value)}
          className="pl-9"
          aria-label="Buscar por nombre de archivo"
          disabled={isLoading}
        />
      </div>

      {/* Docente filter */}
      <div className="min-w-40">
        <Input
          placeholder="Docente..."
          value={docente}
          onChange={(e) => handleDocenteChange(e.target.value)}
          aria-label="Filtrar por docente"
          disabled={isLoading}
        />
      </div>

      {/* Periodo filter */}
      <select
        value={periodo}
        onChange={(e) => handlePeriodoChange(e.target.value)}
        className="h-8 rounded-lg border border-input bg-transparent px-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/50 disabled:opacity-50"
        aria-label="Filtrar por periodo"
        disabled={isLoading}
      >
        <option value="">Todos los períodos</option>
        {periodos.map((p) => (
          <option key={p} value={p}>
            {p}
          </option>
        ))}
      </select>

      {/* Estado filter */}
      <select
        value={estado}
        onChange={(e) =>
          handleEstadoChange(e.target.value as DocumentoEstado | "")
        }
        className="h-8 rounded-lg border border-input bg-transparent px-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/50 disabled:opacity-50"
        aria-label="Filtrar por estado"
        disabled={isLoading}
      >
        <option value="">Todos los estados</option>
        <option value="subido">Subido</option>
        <option value="procesando">Procesando</option>
        <option value="procesado">Procesado</option>
        <option value="error">Error</option>
      </select>

      {/* Clear filters */}
      {hasActiveFilters && (
        <Button
          variant="ghost"
          size="sm"
          onClick={clearAll}
          className="shrink-0"
          aria-label="Limpiar filtros"
        >
          <X className="mr-1 h-3.5 w-3.5" />
          Limpiar
        </Button>
      )}
    </div>
  );
}
