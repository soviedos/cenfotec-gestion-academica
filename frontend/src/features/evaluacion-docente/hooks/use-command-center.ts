"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { fetchDashboardSummary } from "@/features/evaluacion-docente/lib/api/dashboard";
import { fetchEscuelas } from "@/features/evaluacion-docente/lib/api/analytics";
import {
  fetchAlertSummary,
  fetchAlerts,
} from "@/features/evaluacion-docente/lib/api/alertas";
import type {
  AlertaResponse,
  AlertaSummary,
  DashboardSummary,
  Modalidad,
  Severidad,
} from "@/features/evaluacion-docente/types";

interface CommandCenterState {
  dashboard: DashboardSummary | null;
  alertSummary: AlertaSummary | null;
  criticalAlerts: AlertaResponse[];
  isLoading: boolean;
  error: string | null;
}

const INITIAL: CommandCenterState = {
  dashboard: null,
  alertSummary: null,
  criticalAlerts: [],
  isLoading: true,
  error: null,
};

export function useCommandCenter() {
  const [state, setState] = useState<CommandCenterState>(INITIAL);
  const [modalidad, setModalidad] = useState<Modalidad | null>(null);
  const [escuela, setEscuela] = useState<string | null>(null);
  const [escuelas, setEscuelas] = useState<string[]>([]);
  const [severidadFilter, setSeveridadFilter] = useState<Severidad | null>(
    "alta",
  );
  const abortRef = useRef<AbortController | null>(null);
  const alertAbortRef = useRef<AbortController | null>(null);

  // Load available escuelas (re-fetch when modalidad changes)
  useEffect(() => {
    const ctrl = new AbortController();
    fetchEscuelas({ modalidad: modalidad ?? undefined }, ctrl.signal)
      .then(setEscuelas)
      .catch(() => {});
    return () => ctrl.abort();
  }, [modalidad]);

  // Reset escuela when the list no longer contains the selected value
  useEffect(() => {
    if (escuela && escuelas.length > 0 && !escuelas.includes(escuela)) {
      setEscuela(null);
    }
  }, [escuelas, escuela]);

  const fetchAll = useCallback(
    async (mod: Modalidad | null, esc: string | null) => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;
      const signal = controller.signal;

      setState((prev) => ({ ...prev, isLoading: true, error: null }));

      try {
        // Alertas require modalidad (BR-MOD-02); skip when not selected
        const [dashboard, alertSummary, alertsPage] = await Promise.all([
          fetchDashboardSummary(signal, mod, esc),
          mod ? fetchAlertSummary(signal, mod) : Promise.resolve(null),
          mod
            ? fetchAlerts(
                {
                  severidad: "alta",
                  estado: "activa",
                  modalidad: mod,
                  page: 1,
                  page_size: 20,
                },
                signal,
              )
            : Promise.resolve({ items: [], total: 0, page: 1, page_size: 20 }),
        ]);

        // Tendencia is already sorted chronologically by the backend [BR-AN-40]

        if (!signal.aborted) {
          setState({
            dashboard,
            alertSummary,
            criticalAlerts: alertsPage.items ?? [],
            isLoading: false,
            error: null,
          });
        }
      } catch (err: unknown) {
        if (!signal.aborted) {
          setState((prev) => ({
            ...prev,
            isLoading: false,
            error: err instanceof Error ? err.message : "Error loading data",
          }));
        }
      }
    },
    [],
  );

  useEffect(() => {
    fetchAll(modalidad, escuela);
    setSeveridadFilter("alta");
    return () => abortRef.current?.abort();
  }, [fetchAll, modalidad, escuela]);

  // Re-fetch only critical alerts when severidad filter changes
  useEffect(() => {
    if (!modalidad) return;
    alertAbortRef.current?.abort();
    const controller = new AbortController();
    alertAbortRef.current = controller;

    fetchAlerts(
      {
        estado: "activa",
        modalidad,
        severidad: severidadFilter ?? undefined,
        page: 1,
        page_size: 20,
      },
      controller.signal,
    )
      .then((page) => {
        if (!controller.signal.aborted) {
          setState((prev) => ({
            ...prev,
            criticalAlerts: page.items ?? [],
          }));
        }
      })
      .catch(() => {});

    return () => controller.abort();
  }, [severidadFilter, modalidad]);

  return {
    ...state,
    modalidad,
    setModalidad,
    escuela,
    setEscuela,
    escuelas,
    severidadFilter,
    setSeveridadFilter,
    isEmpty:
      !state.isLoading &&
      state.dashboard !== null &&
      state.dashboard.kpis.docentes_evaluados === 0,
    refetch: () => fetchAll(modalidad, escuela),
  };
}
