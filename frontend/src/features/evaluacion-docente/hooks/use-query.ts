"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { postQuery } from "@/features/evaluacion-docente/lib/api/query";
import type {
  QueryHistoryEntry,
  QueryResponse,
} from "@/features/evaluacion-docente/types";

const STORAGE_KEY = "query_history";

interface QueryState {
  response: QueryResponse | null;
  isLoading: boolean;
  error: string | null;
  history: QueryHistoryEntry[];
}

function loadHistory(): QueryHistoryEntry[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as QueryHistoryEntry[];
    return parsed.map((e) => ({ ...e, timestamp: new Date(e.timestamp) }));
  } catch {
    return [];
  }
}

function saveHistory(history: QueryHistoryEntry[]): void {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(history));
  } catch {
    // sessionStorage full or unavailable — ignore
  }
}

export function useQuery() {
  const [state, setState] = useState<QueryState>(() => ({
    response: null,
    isLoading: false,
    error: null,
    history: loadHistory(),
  }));
  const abortRef = useRef<AbortController | null>(null);

  // Persist history on change
  useEffect(() => {
    saveHistory(state.history);
  }, [state.history]);

  const ask = useCallback(async (question: string) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setState((prev) => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await postQuery(
        { question, filters: {} },
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
  }, []);

  const clear = useCallback(() => {
    setState((prev) => ({ ...prev, response: null, error: null }));
  }, []);

  return {
    ...state,
    ask,
    clear,
  };
}
