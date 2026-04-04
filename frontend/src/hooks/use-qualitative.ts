"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  fetchResumenCualitativo,
  fetchComentarios,
  fetchDistribucionTemas,
  fetchDistribucionSentimiento,
} from "@/lib/api/qualitative";
import type {
  ComentarioAnalisis,
  ResumenCualitativo,
  SentimientoDistribucion,
  TemaDistribucion,
} from "@/types";

export interface QualitativeFilters {
  periodo?: string;
  docente?: string;
  asignatura?: string;
  escuela?: string;
  tipo?: string;
  tema?: string;
  sentimiento?: string;
}

interface QualitativeState {
  resumen: ResumenCualitativo | null;
  comentarios: ComentarioAnalisis[];
  temas: TemaDistribucion[];
  sentimientos: SentimientoDistribucion[];
  isLoading: boolean;
  error: string | null;
}

const INITIAL: QualitativeState = {
  resumen: null,
  comentarios: [],
  temas: [],
  sentimientos: [],
  isLoading: true,
  error: null,
};

export function useQualitative(filters: QualitativeFilters = {}) {
  const [state, setState] = useState<QualitativeState>(INITIAL);
  const abortRef = useRef<AbortController | null>(null);
  const filtersKey = JSON.stringify(filters);

  const fetchAll = useCallback(async () => {
    abortRef.current?.abort();
    abortRef.current = new AbortController();

    setState((prev) => ({ ...prev, isLoading: true, error: null }));

    try {
      const [resumen, comentarios, temas, sentimientos] = await Promise.all([
        fetchResumenCualitativo({
          periodo: filters.periodo,
          docente: filters.docente,
          asignatura: filters.asignatura,
          escuela: filters.escuela,
        }),
        fetchComentarios({
          periodo: filters.periodo,
          docente: filters.docente,
          asignatura: filters.asignatura,
          escuela: filters.escuela,
          tipo: filters.tipo,
          tema: filters.tema,
          sentimiento: filters.sentimiento,
          limit: 50,
        }),
        fetchDistribucionTemas({
          periodo: filters.periodo,
          docente: filters.docente,
          asignatura: filters.asignatura,
          escuela: filters.escuela,
          tipo: filters.tipo,
        }),
        fetchDistribucionSentimiento({
          periodo: filters.periodo,
          docente: filters.docente,
          asignatura: filters.asignatura,
          escuela: filters.escuela,
          tipo: filters.tipo,
          tema: filters.tema,
        }),
      ]);

      setState({
        resumen,
        comentarios,
        temas,
        sentimientos,
        isLoading: false,
        error: null,
      });
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      const message =
        err instanceof Error ? err.message : "Error al cargar análisis cualitativo";
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
      state.resumen.total_comentarios === 0,
    refetch: fetchAll,
  };
}
