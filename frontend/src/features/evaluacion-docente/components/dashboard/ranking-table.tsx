"use client";

import { Trophy } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { RankingDocente } from "@/features/evaluacion-docente/types";

interface RankingTableProps {
  data: RankingDocente[];
}

export function RankingTable({ data }: RankingTableProps) {
  if (data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Trophy className="size-4" />
            Ranking docentes
          </CardTitle>
          <CardDescription>Top docentes por promedio general.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex h-40 items-center justify-center">
            <p className="text-sm text-muted-foreground">
              No hay datos de ranking disponibles.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Trophy className="size-4" />
          Ranking docentes
        </CardTitle>
        <CardDescription>Top docentes por promedio general.</CardDescription>
      </CardHeader>
      <CardContent className="px-0">
        <div className="divide-y">
          {data.map((d) => (
            <div
              key={d.docente_nombre}
              className="flex items-center gap-3 px-4 py-2.5"
            >
              <span
                className={cn(
                  "flex size-7 shrink-0 items-center justify-center rounded-full text-xs font-bold",
                  d.posicion === 1 && "bg-amber-100 text-amber-700",
                  d.posicion === 2 && "bg-slate-100 text-slate-600",
                  d.posicion === 3 && "bg-orange-100 text-orange-700",
                  d.posicion > 3 && "bg-muted text-muted-foreground",
                )}
              >
                {d.posicion}
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">
                  {d.docente_nombre}
                </p>
                <p className="text-xs text-muted-foreground">
                  {d.evaluaciones_count}{" "}
                  {d.evaluaciones_count !== 1 ? "evaluaciones" : "evaluación"}
                </p>
              </div>
              <span className="text-sm font-semibold tabular-nums">
                {d.promedio}%
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
