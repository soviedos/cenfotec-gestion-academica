"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { fetchDashboardSummary } from "@/lib/api/dashboard";
import { fetchAlertSummary, fetchAlerts } from "@/lib/api/alertas";
import { sortByPeriodo } from "@/lib/periodo-sort";
import type {
  AlertaResponse,
  AlertaSummary,
  DashboardSummary,
  Modalidad,
} from "@/types";

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
  const abortRef = useRef<AbortController | null>(null);

  const fetchAll = useCallback(async (mod: Modalidad | null) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    const signal = controller.signal;

    setState((prev) => ({ ...prev, isLoading: true, error: null }));

    try {
      const [dashboard, alertSummary, alertsPage] = await Promise.all([
        fetchDashboardSummary(signal, mod),
        fetchAlertSummary(signal, mod),
        fetchAlerts(
          {
            severidad: "alta",
            estado: "activa",
            ...(mod ? { modalidad: mod } : {}),
            page: 1,
            page_size: 10,
          },
          signal,
        ),
      ]);

      // Sort tendencia chronologically [BR-AN-40]
      if (dashboard.tendencia) {
        dashboard.tendencia = sortByPeriodo(dashboard.tendencia);
      }

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
  }, []);

  useEffect(() => {
    fetchAll(modalidad);
    return () => abortRef.current?.abort();
  }, [fetchAll, modalidad]);

  return {
    ...state,
    modalidad,
    setModalidad,
    isEmpty:
      !state.isLoading &&
      state.dashboard !== null &&
      state.dashboard.kpis.docentes_evaluados === 0,
    refetch: () => fetchAll(modalidad),
  };
}
