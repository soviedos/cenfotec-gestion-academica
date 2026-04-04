"use client";

import { createColumnHelper } from "@tanstack/react-table";
import { ArrowUpDown, FileText } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Documento, DocumentoEstado } from "@/types";

const columnHelper = createColumnHelper<Documento>();

function formatFileSize(bytes: number | null): string {
  if (bytes === null || bytes === undefined) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(dateStr: string): string {
  return new Intl.DateTimeFormat("es-CR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(dateStr));
}

const estadoConfig: Record<
  DocumentoEstado,
  { label: string; variant: "default" | "secondary" | "destructive" | "outline" }
> = {
  subido: { label: "Subido", variant: "secondary" },
  procesando: { label: "Procesando", variant: "default" },
  procesado: { label: "Procesado", variant: "outline" },
  error: { label: "Error", variant: "destructive" },
};

export function EstadoBadge({ estado }: { estado: DocumentoEstado }) {
  const config = estadoConfig[estado];
  return (
    <Badge variant={config.variant} data-testid="estado-badge">
      {config.label}
    </Badge>
  );
}

interface SortableHeaderProps {
  label: string;
  field: string;
  currentSort: string;
  currentOrder: string;
  onSort: (field: string) => void;
}

function SortableHeader({
  label,
  field,
  currentSort,
  currentOrder,
  onSort,
}: SortableHeaderProps) {
  const isActive = currentSort === field;
  return (
    <Button
      variant="ghost"
      size="sm"
      className="-ml-3 h-8 font-medium"
      onClick={() => onSort(field)}
      aria-label={`Ordenar por ${label}`}
    >
      {label}
      <ArrowUpDown
        className={`ml-1.5 h-3.5 w-3.5 ${isActive ? "text-foreground" : "text-muted-foreground/50"}`}
      />
      {isActive && (
        <span className="sr-only">
          {currentOrder === "asc" ? "(ascendente)" : "(descendente)"}
        </span>
      )}
    </Button>
  );
}

export function getColumns(
  sortBy: string,
  sortOrder: string,
  onSort: (field: string) => void,
) {
  return [
    columnHelper.display({
      id: "icon",
      cell: () => (
        <FileText className="h-4 w-4 text-muted-foreground" />
      ),
      size: 40,
    }),
    columnHelper.accessor("nombre_archivo", {
      header: () => (
        <SortableHeader
          label="Nombre"
          field="nombre_archivo"
          currentSort={sortBy}
          currentOrder={sortOrder}
          onSort={onSort}
        />
      ),
      cell: (info) => (
        <span className="font-medium" title={info.getValue()}>
          {info.getValue()}
        </span>
      ),
    }),
    columnHelper.accessor("estado", {
      header: "Estado",
      cell: (info) => <EstadoBadge estado={info.getValue()} />,
      size: 120,
    }),
    columnHelper.accessor("tamano_bytes", {
      header: () => (
        <SortableHeader
          label="Tamaño"
          field="tamano_bytes"
          currentSort={sortBy}
          currentOrder={sortOrder}
          onSort={onSort}
        />
      ),
      cell: (info) => (
        <span className="text-muted-foreground">
          {formatFileSize(info.getValue())}
        </span>
      ),
      size: 100,
    }),
    columnHelper.accessor("created_at", {
      header: () => (
        <SortableHeader
          label="Fecha de carga"
          field="created_at"
          currentSort={sortBy}
          currentOrder={sortOrder}
          onSort={onSort}
        />
      ),
      cell: (info) => (
        <span className="text-muted-foreground">{formatDate(info.getValue())}</span>
      ),
      size: 180,
    }),
  ];
}
