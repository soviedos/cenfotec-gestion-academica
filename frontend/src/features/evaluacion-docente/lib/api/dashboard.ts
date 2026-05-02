import { apiClient } from "@/lib/api-client";
import type {
  DashboardSummary,
  Modalidad,
} from "@/features/evaluacion-docente/types";

export async function fetchDashboardSummary(
  signal?: AbortSignal,
  modalidad?: Modalidad | null,
  escuela?: string | null,
): Promise<DashboardSummary> {
  const params = new URLSearchParams();
  if (modalidad) params.set("modalidad", modalidad);
  if (escuela) params.set("escuela", escuela);
  const qs = params.toString();
  return apiClient.get<DashboardSummary>(
    `/api/v1/dashboard/summary${qs ? `?${qs}` : ""}`,
    signal,
  );
}
