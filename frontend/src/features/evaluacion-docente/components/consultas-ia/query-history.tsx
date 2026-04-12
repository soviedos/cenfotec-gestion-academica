"use client";

import { Clock } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { QueryHistoryEntry } from "@/features/evaluacion-docente/types";

interface QueryHistoryProps {
  history: QueryHistoryEntry[];
  onSelect: (question: string) => void;
}

export function QueryHistory({ history, onSelect }: QueryHistoryProps) {
  if (history.length === 0) return null;

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base font-semibold">
          <Clock className="h-4 w-4" />
          Historial de consultas
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-1">
          {history.map((entry, i) => (
            <li key={i}>
              <button
                onClick={() => onSelect(entry.question)}
                className="w-full rounded-md px-3 py-2 text-left text-sm transition-colors hover:bg-muted"
              >
                <span className="line-clamp-1">{entry.question}</span>
                <span className="mt-0.5 block text-xs text-muted-foreground">
                  {entry.timestamp.toLocaleTimeString()}
                </span>
              </button>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
