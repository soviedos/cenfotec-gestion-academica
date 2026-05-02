import { apiClient } from "@/lib/api-client";
import { buildQuery } from "@/lib/query-builder";
import type {
  Caso,
  CasoCreatePayload,
  CasoDetalle,
  CasoEstadoUpdatePayload,
  CasoFilterParams,
  PaginatedResponse,
} from "@/features/convalidaciones/types";

const BASE = "/api/v1/convalidaciones";

// ── CRUD de casos ────────────────────────────────────────────────────

export async function listCasos(
  params: CasoFilterParams = {},
  signal?: AbortSignal,
): Promise<PaginatedResponse<Caso>> {
  return apiClient.get<PaginatedResponse<Caso>>(
    `${BASE}/casos${buildQuery(params)}`,
    signal,
  );
}

export async function crearCaso(
  payload: CasoCreatePayload,
  signal?: AbortSignal,
): Promise<CasoDetalle> {
  return apiClient.post<CasoDetalle>(`${BASE}/casos`, payload, signal);
}

export async function fetchCaso(
  id: string,
  signal?: AbortSignal,
): Promise<CasoDetalle> {
  return apiClient.get<CasoDetalle>(`${BASE}/casos/${id}`, signal);
}

/**
 * Transiciona el estado del caso (e.g., pendiente → procesando → aprobado).
 * Puede incluir observaciones opcionales para el historial de auditoría.
 */
export async function actualizarEstadoCaso(
  id: string,
  payload: CasoEstadoUpdatePayload,
  signal?: AbortSignal,
): Promise<CasoDetalle> {
  return apiClient.patch<CasoDetalle>(
    `${BASE}/casos/${id}/estado`,
    payload,
    signal,
  );
}
