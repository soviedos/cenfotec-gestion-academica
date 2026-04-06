import { apiClient } from "@/lib/api-client";
import type {
  AlertaResponse,
  AlertaSummary,
  AlertFilters,
  Modalidad,
  PaginatedResponse,
} from "@/types";

function buildQuery(params: Record<string, string | number | undefined>) {
  const sp = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      sp.set(key, String(value));
    }
  }
  const q = sp.toString();
  return q ? `?${q}` : "";
}

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

export async function patchAlertEstado(
  alertaId: string,
  estado: string,
): Promise<AlertaResponse> {
  return apiClient.patch<AlertaResponse>(
    `/api/v1/alertas/${alertaId}/estado?estado=${encodeURIComponent(estado)}`,
    {},
  );
}
