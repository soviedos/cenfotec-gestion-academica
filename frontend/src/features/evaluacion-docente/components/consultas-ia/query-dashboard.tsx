"use client";

import { useState } from "react";
import { Sparkles } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useQuery } from "@/features/evaluacion-docente/hooks/use-query";
import { DEFAULT_MODALIDAD, MODALIDADES } from "@/features/evaluacion-docente/lib/business-rules";
import type { Modalidad } from "@/features/evaluacion-docente/types";
import { QueryInput } from "./query-input";
import { QueryResponseCard } from "./query-response";
import { QueryEvidenceList } from "./query-evidence";
import { QueryHistory } from "./query-history";
import { QuerySkeleton, QueryError } from "./query-states";

export function QueryDashboard() {
  const [modalidad, setModalidad] = useState<Modalidad>(DEFAULT_MODALIDAD);
  const { response, isLoading, error, history, ask, clear } =
    useQuery(modalidad);

  return (
    <div className="space-y-6">
      {/* Input */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5" />
                Asistente inteligente
              </CardTitle>
              <CardDescription>
                Usa el modelo Gemini para consultar y analizar la información
                recopilada de las evaluaciones.
              </CardDescription>
            </div>
            <Select
              value={modalidad}
              onValueChange={(v) => setModalidad(v as Modalidad)}
            >
              <SelectTrigger className="w-44">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {MODALIDADES.map((m) => (
                  <SelectItem key={m.value} value={m.value}>
                    {m.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          <QueryInput onSubmit={ask} isLoading={isLoading} />
        </CardContent>
      </Card>

      {/* Loading */}
      {isLoading && <QuerySkeleton />}

      {/* Error */}
      {error && (
        <QueryError
          message={error}
          onRetry={() =>
            history.length > 0 ? ask(history[0].question) : clear()
          }
        />
      )}

      {/* Response */}
      {response && !isLoading && (
        <>
          <QueryResponseCard response={response} />
          <QueryEvidenceList evidence={response.evidence} />
        </>
      )}

      {/* History */}
      <QueryHistory history={history} onSelect={ask} />
    </div>
  );
}
