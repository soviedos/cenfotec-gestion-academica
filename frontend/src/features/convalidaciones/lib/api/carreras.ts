import { apiClient } from "@/lib/api-client";
import { buildQuery } from "@/lib/query-builder";
import type {
  Carrera,
  Malla,
  MallaDetalle,
  PaginatedResponse,
} from "@/features/convalidaciones/types";

const BASE = "/api/v1/convalidaciones";

// ── Carreras ─────────────────────────────────────────────────────────

export async function listCarreras(
  params: { activa?: boolean; page?: number; page_size?: number } = {},
  signal?: AbortSignal,
): Promise<PaginatedResponse<Carrera>> {
  return apiClient.get<PaginatedResponse<Carrera>>(
    `${BASE}/carreras${buildQuery(params)}`,
    signal,
  );
}

export async function fetchCarrera(
  id: string,
  signal?: AbortSignal,
): Promise<Carrera> {
  return apiClient.get<Carrera>(`${BASE}/carreras/${id}`, signal);
}

// ── Mallas curriculares ──────────────────────────────────────────────

export async function listMallas(
  params: { carrera_id?: string; activa?: boolean } = {},
  signal?: AbortSignal,
): Promise<Malla[]> {
  return apiClient.get<Malla[]>(`${BASE}/mallas${buildQuery(params)}`, signal);
}

/**
 * Carga (crea) una malla curricular para una carrera.
 * El cuerpo es un JSON con la estructura de la malla.
 */
export async function cargarMalla(
  payload: Omit<Malla, "id" | "created_at" | "updated_at">,
  signal?: AbortSignal,
): Promise<Malla> {
  return apiClient.post<Malla>(`${BASE}/mallas`, payload, signal);
}

/**
 * Retorna la malla curricular vigente de una carrera,
 * incluyendo la lista completa de cursos.
 */
export async function fetchMallaVigente(
  carreraId: string,
  signal?: AbortSignal,
): Promise<MallaDetalle> {
  return apiClient.get<MallaDetalle>(
    `${BASE}/carreras/${carreraId}/malla-vigente`,
    signal,
  );
}
