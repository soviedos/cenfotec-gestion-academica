import { apiClient } from "@/lib/api-client";
import { buildQuery } from "@/lib/api/query-builder";
import type {
  DimensionPromedio,
  DocentePromedio,
  PeriodoMetrica,
  RankingDocente,
  ResumenGeneral,
} from "@/types";

export async function fetchResumen(
  periodo?: string,
  signal?: AbortSignal,
  modalidad?: string,
  escuela?: string,
  curso?: string,
): Promise<ResumenGeneral> {
  return apiClient.get<ResumenGeneral>(
    `/api/v1/analytics/resumen${buildQuery({ periodo, modalidad, escuela, curso })}`,
    signal,
  );
}

export async function fetchDocentePromedios(
  params: {
    periodo?: string;
    modalidad?: string;
    escuela?: string;
    curso?: string;
    limit?: number;
    offset?: number;
  },
  signal?: AbortSignal,
): Promise<DocentePromedio[]> {
  return apiClient.get<DocentePromedio[]>(
    `/api/v1/analytics/docentes${buildQuery(params)}`,
    signal,
  );
}

export async function fetchDimensiones(
  params: {
    periodo?: string;
    modalidad?: string;
    escuela?: string;
    curso?: string;
    docente?: string;
  },
  signal?: AbortSignal,
): Promise<DimensionPromedio[]> {
  return apiClient.get<DimensionPromedio[]>(
    `/api/v1/analytics/dimensiones${buildQuery(params)}`,
    signal,
  );
}

export async function fetchEvolucion(
  docente?: string,
  signal?: AbortSignal,
  modalidad?: string,
  escuela?: string,
  curso?: string,
): Promise<PeriodoMetrica[]> {
  return apiClient.get<PeriodoMetrica[]>(
    `/api/v1/analytics/evolucion${buildQuery({ docente, modalidad, escuela, curso })}`,
    signal,
  );
}

export async function fetchRanking(
  params: {
    periodo?: string;
    modalidad?: string;
    escuela?: string;
    curso?: string;
    limit?: number;
  },
  signal?: AbortSignal,
): Promise<RankingDocente[]> {
  return apiClient.get<RankingDocente[]>(
    `/api/v1/analytics/ranking${buildQuery(params)}`,
    signal,
  );
}

export async function fetchEscuelas(
  params: { modalidad?: string; periodo?: string },
  signal?: AbortSignal,
): Promise<string[]> {
  return apiClient.get<string[]>(
    `/api/v1/analytics/escuelas${buildQuery(params)}`,
    signal,
  );
}

export async function fetchCursos(
  params: { escuela?: string; modalidad?: string; periodo?: string },
  signal?: AbortSignal,
): Promise<string[]> {
  return apiClient.get<string[]>(
    `/api/v1/analytics/cursos${buildQuery(params)}`,
    signal,
  );
}
