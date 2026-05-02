"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  fetchResumen,
  fetchDocentePromedios,
  fetchDimensiones,
  fetchEvolucion,
  fetchRanking,
} from "@/features/evaluacion-docente/lib/api/analytics";
import type {
  DimensionPromedio,
  DocentePromedio,
  PeriodoMetrica,
  RankingDocente,
  ResumenGeneral,
} from "@/features/evaluacion-docente/types";

export interface AnalyticsFilters {
  periodo?: string;
  modalidad?: string;
  escuela?: string;
  curso?: string;
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
  const filtersRef = useRef(filters);
  filtersRef.current = filters;

  const fetchAll = useCallback(async () => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    const { signal } = controller;

    setState((prev) => ({ ...prev, isLoading: true, error: null }));

    try {
      const f = filtersRef.current;

      // Fire all requests in parallel but settle progressively
      const resumenP = fetchResumen(
        f.periodo,
        signal,
        f.modalidad,
        f.escuela,
        f.curso,
      ).then((resumen) => {
        setState((prev) => ({ ...prev, resumen }));
      });
      const docentesP = fetchDocentePromedios(
        {
          periodo: f.periodo,
          modalidad: f.modalidad,
          escuela: f.escuela,
          curso: f.curso,
          limit: 20,
        },
        signal,
      ).then((docentes) => {
        setState((prev) => ({ ...prev, docentes }));
      });
      const dimensionesP = fetchDimensiones(
        {
          periodo: f.periodo,
          modalidad: f.modalidad,
          escuela: f.escuela,
          curso: f.curso,
        },
        signal,
      ).then((dimensiones) => {
        setState((prev) => ({ ...prev, dimensiones }));
      });
      const evolucionP = fetchEvolucion(
        undefined,
        signal,
        f.modalidad,
        f.escuela,
        f.curso,
      ).then((evolucion) => {
        setState((prev) => ({
          ...prev,
          evolucion,
        }));
      });
      const rankingP = fetchRanking(
        {
          periodo: f.periodo,
          modalidad: f.modalidad,
          escuela: f.escuela,
          curso: f.curso,
          limit: 10,
        },
        signal,
      ).then((ranking) => {
        setState((prev) => ({ ...prev, ranking }));
      });

      await Promise.all([
        resumenP,
        docentesP,
        dimensionesP,
        evolucionP,
        rankingP,
      ]);

      setState((prev) => ({ ...prev, isLoading: false, error: null }));
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      const message =
        err instanceof Error ? err.message : "Error al cargar analytics";
      setState((prev) => ({ ...prev, isLoading: false, error: message }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtersKey]);

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
