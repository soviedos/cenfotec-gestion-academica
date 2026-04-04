"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  fetchResumen,
  fetchDocentePromedios,
  fetchDimensiones,
  fetchEvolucion,
  fetchRanking,
} from "@/lib/api/analytics";
import type {
  DimensionPromedio,
  DocentePromedio,
  PeriodoMetrica,
  RankingDocente,
  ResumenGeneral,
} from "@/types";

export interface AnalyticsFilters {
  periodo?: string;
}

interface AnalyticsState {
  resumen: ResumenGeneral | null;
  docentes: DocentePromedio[];
  dimensiones: DimensionPromedio[];
  evolucion: PeriodoMetrica[];
  ranking: RankingDocente[];
  isLoading: boolean;
  error: string | null;
}

const INITIAL: AnalyticsState = {
  resumen: null,
  docentes: [],
  dimensiones: [],
  evolucion: [],
  ranking: [],
  isLoading: true,
  error: null,
};

export function useAnalytics(filters: AnalyticsFilters = {}) {
  const [state, setState] = useState<AnalyticsState>(INITIAL);
  const abortRef = useRef<AbortController | null>(null);
  const filtersKey = JSON.stringify(filters);

  const fetchAll = useCallback(async () => {
    abortRef.current?.abort();
    abortRef.current = new AbortController();

    setState((prev) => ({ ...prev, isLoading: true, error: null }));

    try {
      const [resumen, docentes, dimensiones, evolucion, ranking] =
        await Promise.all([
          fetchResumen(filters.periodo),
          fetchDocentePromedios({ periodo: filters.periodo, limit: 20 }),
          fetchDimensiones({ periodo: filters.periodo }),
          fetchEvolucion(),
          fetchRanking({ periodo: filters.periodo, limit: 10 }),
        ]);

      setState({
        resumen,
        docentes,
        dimensiones,
        evolucion,
        ranking,
        isLoading: false,
        error: null,
      });
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      const message =
        err instanceof Error ? err.message : "Error al cargar analytics";
      setState((prev) => ({ ...prev, isLoading: false, error: message }));
    }
  }, [filtersKey]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    fetchAll();
    return () => abortRef.current?.abort();
  }, [fetchAll]);

  return {
    ...state,
    isEmpty:
      !state.isLoading &&
      state.resumen !== null &&
      state.resumen.total_evaluaciones === 0,
    refetch: fetchAll,
  };
}
