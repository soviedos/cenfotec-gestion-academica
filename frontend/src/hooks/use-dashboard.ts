"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { fetchDashboardSummary } from "@/lib/api/dashboard";
import type { DashboardSummary } from "@/types";

interface DashboardState {
  data: DashboardSummary | null;
  isLoading: boolean;
  error: string | null;
}

const INITIAL: DashboardState = {
  data: null,
  isLoading: true,
  error: null,
};

export function useDashboard() {
  const [state, setState] = useState<DashboardState>(INITIAL);
  const abortRef = useRef<AbortController | null>(null);

  const fetchAll = useCallback(async () => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setState((prev) => ({ ...prev, isLoading: true, error: null }));

    try {
      const data = await fetchDashboardSummary(controller.signal);
      setState({ data, isLoading: false, error: null });
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      const message =
        err instanceof Error ? err.message : "Error al cargar el dashboard";
      setState((prev) => ({ ...prev, isLoading: false, error: message }));
    }
  }, []);

  useEffect(() => {
    fetchAll();
    return () => abortRef.current?.abort();
  }, [fetchAll]);

  return {
    ...state,
    isEmpty:
      !state.isLoading &&
      state.data !== null &&
      state.data.kpis.docentes_evaluados === 0,
    refetch: fetchAll,
  };
}
