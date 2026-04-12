"use client";

import { useEffect, useState } from "react";
import { Copy } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { listDuplicados } from "@/features/evaluacion-docente/lib/api/documents";
import type { DuplicadoRead } from "@/features/evaluacion-docente/types";

interface DuplicadoBadgeProps {
  documentoId: string;
  posibleDuplicado: boolean;
}

export function DuplicadoBadge({
  documentoId,
  posibleDuplicado,
}: DuplicadoBadgeProps) {
  const [duplicados, setDuplicados] = useState<DuplicadoRead[] | null>(null);
  const [loaded, setLoaded] = useState(false);

  // Lazy-load duplicado details on first hover
  const handleOpen = () => {
    if (loaded) return;
    setLoaded(true);
    listDuplicados(documentoId)
      .then(setDuplicados)
      .catch(() => setDuplicados([]));
  };

  if (!posibleDuplicado) return null;

  return (
    <TooltipProvider delay={200}>
      <Tooltip>
        <TooltipTrigger
          render={
            <button
              onMouseEnter={handleOpen}
              onFocus={handleOpen}
              className="inline-flex cursor-default"
              aria-label="Posible duplicado"
            />
          }
        >
          <Badge
            variant="outline"
            className="border-amber-500/50 bg-amber-50 text-amber-700 dark:bg-amber-950/30 dark:text-amber-400"
            data-testid="duplicado-badge"
          >
            <Copy className="mr-1 h-3 w-3" />
            Duplicado
          </Badge>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="max-w-xs">
          {!duplicados ? (
            <p className="text-xs">Cargando...</p>
          ) : duplicados.length === 0 ? (
            <p className="text-xs">Marcado como posible duplicado</p>
          ) : (
            <div className="space-y-1">
              <p className="text-xs font-medium">
                Coincide con {duplicados.length}{" "}
                {duplicados.length === 1 ? "documento" : "documentos"}:
              </p>
              <ul className="space-y-0.5">
                {duplicados.map((d) => (
                  <li key={d.id} className="text-xs text-muted-foreground">
                    {d.documento_coincidente.nombre_archivo}
                    <span className="ml-1 text-[10px] opacity-70">
                      ({Math.round(d.score * 100)}%)
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
