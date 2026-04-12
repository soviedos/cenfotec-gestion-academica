import { apiClient } from "@/lib/api-client";
import { buildQuery } from "@/features/evaluacion-docente/lib/api/query-builder";
import type {
  AlertaResponse,
  AlertaSummary,
  AlertFilters,
  Modalidad,
  PaginatedResponse,
} from "@/features/evaluacion-docente/types";

export async function fetchAlertSummary(
  signal?: AbortSignal,
  modalidad?: Modalidad | null,
): Promise<AlertaSummary> {
  const params = modalidad ? `?modalidad=${encodeURIComponent(modalidad)}` : "";
  return apiClient.get<AlertaSummary>(
    `/api/v1/alertas/summary${params}`,
    signal,
  );
}

export async function fetchAlerts(
  filters: AlertFilters = {},
  signal?: AbortSignal,
): Promise<PaginatedResponse<AlertaResponse>> {
  return apiClient.get<PaginatedResponse<AlertaResponse>>(
    `/api/v1/alertas${buildQuery(filters as Record<string, string | number | undefined>)}`,
    signal,
  );
}
