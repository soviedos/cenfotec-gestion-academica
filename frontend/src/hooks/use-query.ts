"use client";

import { useCallback, useRef, useState } from "react";
import { postQuery } from "@/lib/api/query";
import type { Modalidad, QueryHistoryEntry, QueryResponse } from "@/types";

interface QueryState {
  response: QueryResponse | null;
  isLoading: boolean;
  error: string | null;
  history: QueryHistoryEntry[];
}

const INITIAL: QueryState = {
  response: null,
  isLoading: false,
  error: null,
  history: [],
};

export function useQuery(modalidad: Modalidad) {
  const [state, setState] = useState<QueryState>(INITIAL);
  const abortRef = useRef<AbortController | null>(null);

  const ask = useCallback(
    async (question: string) => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setState((prev) => ({ ...prev, isLoading: true, error: null }));

      try {
        const response = await postQuery(
          { question, filters: { modalidad } },
          controller.signal,
        );

        const entry: QueryHistoryEntry = {
          question,
          response,
          timestamp: new Date(),
        };

        setState((prev) => ({
          response,
          isLoading: false,
          error: null,
          history: [entry, ...prev.history],
        }));
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") return;
        const message =
          err instanceof Error ? err.message : "Error al procesar la consulta";
        setState((prev) => ({ ...prev, isLoading: false, error: message }));
      }
    },
    [modalidad],
  );

  const clear = useCallback(() => {
    setState((prev) => ({ ...prev, response: null, error: null }));
  }, []);

  return {
    ...state,
    ask,
    clear,
  };
}
