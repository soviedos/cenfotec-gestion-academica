import { apiClient } from "@/lib/api-client";
import type { DashboardSummary, Modalidad } from "@/features/evaluacion-docente/types";

export async function fetchDashboardSummary(
  signal?: AbortSignal,
  modalidad?: Modalidad | null,
): Promise<DashboardSummary> {
  const params = modalidad ? `?modalidad=${encodeURIComponent(modalidad)}` : "";
  return apiClient.get<DashboardSummary>(
    `/api/v1/dashboard/summary${params}`,
    signal,
  );
}
