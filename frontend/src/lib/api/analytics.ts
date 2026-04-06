import { apiClient } from "@/lib/api-client";
import type {
  DimensionPromedio,
  DocentePromedio,
  PeriodoMetrica,
  RankingDocente,
  ResumenGeneral,
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

export async function fetchResumen(
  periodo?: string,
  signal?: AbortSignal,
): Promise<ResumenGeneral> {
  return apiClient.get<ResumenGeneral>(
    `/api/v1/analytics/resumen${buildQuery({ periodo })}`,
    signal,
  );
}

export async function fetchDocentePromedios(
  params: {
    periodo?: string;
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
): Promise<PeriodoMetrica[]> {
  return apiClient.get<PeriodoMetrica[]>(
    `/api/v1/analytics/evolucion${buildQuery({ docente })}`,
    signal,
  );
}

export async function fetchRanking(
  params: {
    periodo?: string;
    limit?: number;
  },
  signal?: AbortSignal,
): Promise<RankingDocente[]> {
  return apiClient.get<RankingDocente[]>(
    `/api/v1/analytics/ranking${buildQuery(params)}`,
    signal,
  );
}
