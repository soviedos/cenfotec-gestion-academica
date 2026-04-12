"use client";

import { fetchDashboardSummary } from "@/features/evaluacion-docente/lib/api/dashboard";
import type { DashboardSummary } from "@/features/evaluacion-docente/types";
import { useApiFetch } from "@/hooks/use-api-fetch";

export function useDashboard() {
  const { data, isLoading, error, refetch } = useApiFetch<DashboardSummary>(
    (signal) => fetchDashboardSummary(signal),
    [],
    "Error al cargar el dashboard",
  );

  return {
    data,
    isLoading,
    error,
    isEmpty: !isLoading && data !== null && data.kpis.docentes_evaluados === 0,
    refetch,
  };
}
