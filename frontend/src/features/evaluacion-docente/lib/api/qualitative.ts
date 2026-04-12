import { apiClient } from "@/lib/api-client";
import { buildQuery } from "@/features/evaluacion-docente/lib/api/query-builder";
import type {
  ComentarioAnalisis,
  FiltrosCualitativos,
  NubePalabras,
  ResumenCualitativo,
  SentimientoDistribucion,
  TemaDistribucion,
} from "@/features/evaluacion-docente/types";

export async function fetchFiltrosCualitativos(
  signal?: AbortSignal,
): Promise<FiltrosCualitativos> {
  return apiClient.get<FiltrosCualitativos>(
    `/api/v1/qualitative/filtros`,
    signal,
  );
}

export async function fetchResumenCualitativo(
  params: {
    modalidad?: string;
    periodo?: string;
    docente?: string;
    asignatura?: string;
    escuela?: string;
  },
  signal?: AbortSignal,
): Promise<ResumenCualitativo> {
  return apiClient.get<ResumenCualitativo>(
    `/api/v1/qualitative/resumen${buildQuery(params)}`,
    signal,
  );
}

export async function fetchComentarios(
  params: {
    modalidad?: string;
    periodo?: string;
    docente?: string;
    asignatura?: string;
    escuela?: string;
    tipo?: string;
    tema?: string;
    sentimiento?: string;
    limit?: number;
    offset?: number;
  },
  signal?: AbortSignal,
): Promise<ComentarioAnalisis[]> {
  return apiClient.get<ComentarioAnalisis[]>(
    `/api/v1/qualitative/comentarios${buildQuery(params)}`,
    signal,
  );
}

export async function fetchDistribucionTemas(
  params: {
    modalidad?: string;
    periodo?: string;
    docente?: string;
    asignatura?: string;
    escuela?: string;
    tipo?: string;
  },
  signal?: AbortSignal,
): Promise<TemaDistribucion[]> {
  return apiClient.get<TemaDistribucion[]>(
    `/api/v1/qualitative/distribucion/temas${buildQuery(params)}`,
    signal,
  );
}

export async function fetchDistribucionSentimiento(
  params: {
    modalidad?: string;
    periodo?: string;
    docente?: string;
    asignatura?: string;
    escuela?: string;
    tipo?: string;
    tema?: string;
  },
  signal?: AbortSignal,
): Promise<SentimientoDistribucion[]> {
  return apiClient.get<SentimientoDistribucion[]>(
    `/api/v1/qualitative/distribucion/sentimiento${buildQuery(params)}`,
    signal,
  );
}

export async function fetchNubePalabras(
  params: {
    modalidad?: string;
    periodo?: string;
    docente?: string;
    asignatura?: string;
    escuela?: string;
    tipo?: string;
  },
  signal?: AbortSignal,
): Promise<NubePalabras> {
  return apiClient.get<NubePalabras>(
    `/api/v1/qualitative/nube-palabras${buildQuery(params)}`,
    signal,
  );
}
