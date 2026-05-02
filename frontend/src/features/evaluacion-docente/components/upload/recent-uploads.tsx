"use client";

import Link from "next/link";
import { Loader2, Library, ArrowRight, Trash2 } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EstadoBadge } from "@/features/evaluacion-docente/components/biblioteca/columns";
import type { Documento } from "@/features/evaluacion-docente/types";

interface RecentUploadsProps {
  documents: Documento[];
  total: number;
  isLoading: boolean;
  isEmpty: boolean;
  onClear?: () => void;
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

export function RecentUploads({
  documents,
  total,
  isLoading,
  isEmpty,
  onClear,
}: RecentUploadsProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              Documentos recientes
              {!isLoading && (
                <Badge variant="secondary" className="font-normal">
                  {total}
                </Badge>
              )}
            </CardTitle>
            <CardDescription>
              Últimos PDFs cargados en la plataforma.
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            {!isEmpty && !isLoading && onClear && (
              <Button variant="ghost" size="sm" onClick={onClear}>
                <Trash2 className="mr-1.5 h-3.5 w-3.5" />
                Limpiar
              </Button>
            )}
            <Link href="/evaluacion-docente/biblioteca">
              <Button variant="outline" size="sm">
                Ver biblioteca
                <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
              </Button>
            </Link>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex flex-col items-center justify-center gap-2 py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            <span className="text-sm text-muted-foreground">
              Cargando documentos...
            </span>
          </div>
        ) : isEmpty ? (
          <div className="flex flex-col items-center justify-center gap-2 py-8">
            <Library className="h-8 w-8 text-muted-foreground/40" />
            <span className="text-sm text-muted-foreground">
              No se han cargado documentos aún
            </span>
          </div>
        ) : (
          <div
            className="space-y-2"
            role="list"
            aria-label="Documentos recientes"
          >
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center justify-between rounded-lg border px-4 py-2.5"
                role="listitem"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <span className="truncate text-sm font-medium">
                    {doc.nombre_archivo}
                  </span>
                  <EstadoBadge estado={doc.estado} />
                </div>
                <span className="shrink-0 text-xs text-muted-foreground">
                  {formatDate(doc.created_at)}
                </span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
