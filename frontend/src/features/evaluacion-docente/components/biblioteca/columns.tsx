"use client";

import { useState } from "react";
import { createColumnHelper } from "@tanstack/react-table";
import { ArrowUpDown, Copy, Check, Eye, FileText, Trash2 } from "lucide-react";
import { getDocumentDownloadUrl } from "@/features/evaluacion-docente/lib/api/documents";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DuplicadoBadge } from "./duplicado-badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import type { Documento, DocumentoEstado } from "@/features/evaluacion-docente/types";

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
  {
    label: string;
    variant: "default" | "secondary" | "destructive" | "outline";
  }
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

function CopyableSha({ sha }: { sha: string }) {
  const [copied, setCopied] = useState(false);
  const short = sha.slice(0, 12);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(sha);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <TooltipProvider delay={200}>
      <Tooltip>
        <TooltipTrigger
          render={
            <button
              onClick={handleCopy}
              className="inline-flex items-center gap-1 rounded px-1.5 py-0.5 font-mono text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              aria-label={`Copiar SHA: ${sha}`}
            />
          }
        >
          {short}…
          {copied ? (
            <Check className="h-3 w-3 text-green-500" />
          ) : (
            <Copy className="h-3 w-3" />
          )}
        </TooltipTrigger>
        <TooltipContent side="top" className="font-mono text-xs">
          {sha}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

function ViewPdfButton({ documento }: { documento: Documento }) {
  const handleView = () => {
    window.open(getDocumentDownloadUrl(documento.id), "_blank", "noopener");
  };

  return (
    <TooltipProvider delay={200}>
      <Tooltip>
        <TooltipTrigger
          render={
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-muted-foreground hover:text-foreground"
              onClick={handleView}
              aria-label={`Ver ${documento.nombre_archivo}`}
            />
          }
        >
          <Eye className="h-4 w-4" />
        </TooltipTrigger>
        <TooltipContent side="top">Ver PDF original</TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

function DeleteButton({
  documento,
  onDelete,
}: {
  documento: Documento;
  onDelete: (id: string) => void;
}) {
  return (
    <AlertDialog>
      <AlertDialogTrigger
        render={
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-muted-foreground hover:text-destructive"
            aria-label={`Eliminar ${documento.nombre_archivo}`}
          />
        }
      >
        <Trash2 className="h-4 w-4" />
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>¿Eliminar documento?</AlertDialogTitle>
          <AlertDialogDescription>
            Se eliminará permanentemente{" "}
            <span className="font-medium text-foreground">
              {documento.nombre_archivo}
            </span>{" "}
            junto con todas sus evaluaciones, dimensiones, cursos y comentarios
            asociados. Esta acción no se puede deshacer.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancelar</AlertDialogCancel>
          <AlertDialogAction
            onClick={() => onDelete(documento.id)}
            className="bg-destructive text-white hover:bg-destructive/90"
          >
            Eliminar
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

export function getColumns(
  sortBy: string,
  sortOrder: string,
  onSort: (field: string) => void,
  onDelete?: (id: string) => void,
) {
  return [
    columnHelper.display({
      id: "icon",
      cell: () => <FileText className="h-4 w-4 text-muted-foreground" />,
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
      cell: (info) => (
        <div className="flex items-center gap-1.5">
          <EstadoBadge estado={info.getValue()} />
          <DuplicadoBadge
            documentoId={info.row.original.id}
            posibleDuplicado={info.row.original.posible_duplicado}
          />
        </div>
      ),
      size: 200,
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
    columnHelper.accessor("hash_sha256", {
      header: "SHA-256",
      cell: (info) => <CopyableSha sha={info.getValue()} />,
      size: 150,
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
        <span className="text-muted-foreground">
          {formatDate(info.getValue())}
        </span>
      ),
      size: 180,
    }),
    columnHelper.display({
      id: "actions",
      header: "",
      cell: (info) => (
        <div className="flex items-center gap-0.5">
          <ViewPdfButton documento={info.row.original} />
          {onDelete && (
            <DeleteButton documento={info.row.original} onDelete={onDelete} />
          )}
        </div>
      ),
      size: 90,
    }),
  ];
}
