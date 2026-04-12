"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { QueryEvidence } from "@/features/evaluacion-docente/types";

interface QueryEvidenceListProps {
  evidence: QueryEvidence[];
}

export function QueryEvidenceList({ evidence }: QueryEvidenceListProps) {
  if (evidence.length === 0) return null;

  const metrics = evidence.filter((e) => e.type === "metric");
  const comments = evidence.filter((e) => e.type === "comment");

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-semibold">
          Evidencias recuperadas
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {metrics.length > 0 && (
          <div>
            <h4 className="mb-2 text-sm font-medium text-muted-foreground">
              Métricas
            </h4>
            <div className="grid gap-2 sm:grid-cols-2">
              {metrics.map((e, i) => {
                if (e.type !== "metric") return null;
                return (
                  <div
                    key={i}
                    className="flex items-center justify-between rounded-lg border px-3 py-2"
                  >
                    <span className="text-sm">{e.label}</span>
                    <span className="font-mono text-sm font-semibold">
                      {e.value.toFixed(2)}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {comments.length > 0 && (
          <div>
            <h4 className="mb-2 text-sm font-medium text-muted-foreground">
              Comentarios
            </h4>
            <div className="space-y-2">
              {comments.map((e, i) => {
                if (e.type !== "comment") return null;
                return (
                  <div key={i} className="rounded-lg border px-3 py-2">
                    <p className="text-sm">{e.texto}</p>
                    <div className="mt-1 flex flex-wrap gap-1.5">
                      <Badge variant="outline" className="text-xs">
                        {e.source.docente}
                      </Badge>
                      <Badge variant="outline" className="text-xs">
                        {e.source.asignatura}
                      </Badge>
                      <Badge variant="outline" className="text-xs">
                        {e.source.fuente}
                      </Badge>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
