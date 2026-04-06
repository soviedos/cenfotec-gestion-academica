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
      const [resumen, comentarios, temas, sentimientos] = await Promise.all([
        fetchResumenCualitativo(
          {
            periodo: f.periodo,
            docente: f.docente,
            asignatura: f.asignatura,
            escuela: f.escuela,
          },
          signal,
        ),
        fetchComentarios(
          {
            periodo: f.periodo,
            docente: f.docente,
            asignatura: f.asignatura,
            escuela: f.escuela,
            tipo: f.tipo,
            tema: f.tema,
            sentimiento: f.sentimiento,
            limit: 50,
          },
          signal,
        ),
        fetchDistribucionTemas(
          {
            periodo: f.periodo,
            docente: f.docente,
            asignatura: f.asignatura,
            escuela: f.escuela,
            tipo: f.tipo,
          },
          signal,
        ),
        fetchDistribucionSentimiento(
          {
            periodo: f.periodo,
            docente: f.docente,
            asignatura: f.asignatura,
            escuela: f.escuela,
            tipo: f.tipo,
            tema: f.tema,
          },
          signal,
        ),
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
        err instanceof Error
          ? err.message
          : "Error al cargar análisis cualitativo";
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
      state.resumen.total_comentarios === 0,
    refetch: fetchAll,
  };
}
