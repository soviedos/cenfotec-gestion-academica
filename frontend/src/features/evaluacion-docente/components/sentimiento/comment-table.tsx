"use client";

import { memo } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  SentimentBadge,
  TipoBadge,
  TemaBadge,
} from "@/features/evaluacion-docente/components/sentimiento/badges";
import type { ComentarioAnalisis } from "@/features/evaluacion-docente/types";

interface CommentTableProps {
  data: ComentarioAnalisis[];
  onTemaClick?: (tema: string) => void;
  onSentimientoClick?: (sentimiento: string) => void;
}

export const CommentTable = memo(function CommentTable({
  data,
  onTemaClick,
  onSentimientoClick,
}: CommentTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Comentarios clasificados</CardTitle>
        <CardDescription>
          {data.length} comentario{data.length !== 1 ? "s" : ""} mostrado
          {data.length !== 1 ? "s" : ""}.
        </CardDescription>
      </CardHeader>
      <CardContent className="px-0">
        {data.length === 0 ? (
          <div className="flex h-40 items-center justify-center">
            <p className="text-sm text-muted-foreground">
              No hay comentarios que coincidan con los filtros.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left">
                  <th className="px-4 py-2.5 font-medium text-muted-foreground">
                    Comentario
                  </th>
                  <th className="px-4 py-2.5 font-medium text-muted-foreground whitespace-nowrap">
                    Tipo
                  </th>
                  <th className="px-4 py-2.5 font-medium text-muted-foreground whitespace-nowrap">
                    Tema
                  </th>
                  <th className="px-4 py-2.5 font-medium text-muted-foreground whitespace-nowrap">
                    Sentimiento
                  </th>
                  <th className="px-4 py-2.5 font-medium text-muted-foreground whitespace-nowrap">
                    Fuente
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {data.map((c) => (
                  <tr
                    key={c.id}
                    className="hover:bg-muted/50 transition-colors"
                  >
                    <td className="px-4 py-3 max-w-md">
                      <p className="line-clamp-2">{c.texto}</p>
                      {c.asignatura && (
                        <p className="mt-0.5 text-xs text-muted-foreground">
                          {c.asignatura}
                        </p>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <TipoBadge value={c.tipo} />
                    </td>
                    <td className="px-4 py-3">
                      <button
                        type="button"
                        className="cursor-pointer"
                        onClick={() => onTemaClick?.(c.tema)}
                      >
                        <TemaBadge value={c.tema} />
                      </button>
                    </td>
                    <td className="px-4 py-3">
                      <button
                        type="button"
                        className="cursor-pointer"
                        onClick={() =>
                          c.sentimiento && onSentimientoClick?.(c.sentimiento)
                        }
                      >
                        <SentimentBadge value={c.sentimiento} />
                      </button>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">
                      {c.fuente}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
});
