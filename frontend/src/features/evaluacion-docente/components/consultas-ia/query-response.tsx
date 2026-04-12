"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { QueryResponse as QueryResponseType } from "@/features/evaluacion-docente/types";

interface QueryResponseProps {
  response: QueryResponseType;
}

export function QueryResponseCard({ response }: QueryResponseProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
        <CardTitle className="text-base font-semibold">Respuesta</CardTitle>
        <div className="flex items-center gap-2">
          {response.confidence !== null && (
            <Badge variant="outline">
              Confianza: {(response.confidence * 100).toFixed(0)}%
            </Badge>
          )}
          <Badge variant="secondary" className="text-xs">
            {response.metadata.model}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="prose prose-sm max-w-none whitespace-pre-wrap text-sm leading-relaxed">
          {/* response.answer is rendered as text node — React escapes it automatically.
              Do NOT use dangerouslySetInnerHTML here. */}
          {response.answer}
        </div>
        <div className="mt-4 flex items-center gap-4 text-xs text-muted-foreground">
          <span>{response.metadata.tokens_used} tokens</span>
          <span>{response.metadata.latency_ms}ms</span>
          <span>{response.evidence.length} evidencias</span>
        </div>
      </CardContent>
    </Card>
  );
}
