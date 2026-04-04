import { apiClient } from "@/lib/api-client";
import type {
  ComentarioAnalisis,
  FiltrosCualitativos,
  NubePalabras,
  ResumenCualitativo,
  SentimientoDistribucion,
  TemaDistribucion,
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

export async function fetchFiltrosCualitativos(): Promise<FiltrosCualitativos> {
  return apiClient.get<FiltrosCualitativos>(`/api/v1/qualitative/filtros`);
}

export async function fetchResumenCualitativo(params: {
  periodo?: string;
  docente?: string;
  asignatura?: string;
  escuela?: string;
}): Promise<ResumenCualitativo> {
  return apiClient.get<ResumenCualitativo>(
    `/api/v1/qualitative/resumen${buildQuery(params)}`,
  );
}

export async function fetchComentarios(params: {
  periodo?: string;
  docente?: string;
  asignatura?: string;
  escuela?: string;
  tipo?: string;
  tema?: string;
  sentimiento?: string;
  limit?: number;
  offset?: number;
}): Promise<ComentarioAnalisis[]> {
  return apiClient.get<ComentarioAnalisis[]>(
    `/api/v1/qualitative/comentarios${buildQuery(params)}`,
  );
}

export async function fetchDistribucionTemas(params: {
  periodo?: string;
  docente?: string;
  asignatura?: string;
  escuela?: string;
  tipo?: string;
}): Promise<TemaDistribucion[]> {
  return apiClient.get<TemaDistribucion[]>(
    `/api/v1/qualitative/distribucion/temas${buildQuery(params)}`,
  );
}

export async function fetchDistribucionSentimiento(params: {
  periodo?: string;
  docente?: string;
  asignatura?: string;
  escuela?: string;
  tipo?: string;
  tema?: string;
}): Promise<SentimientoDistribucion[]> {
  return apiClient.get<SentimientoDistribucion[]>(
    `/api/v1/qualitative/distribucion/sentimiento${buildQuery(params)}`,
  );
}

export async function fetchNubePalabras(params: {
  periodo?: string;
  docente?: string;
  asignatura?: string;
  escuela?: string;
  tipo?: string;
}): Promise<NubePalabras> {
  return apiClient.get<NubePalabras>(
    `/api/v1/qualitative/nube-palabras${buildQuery(params)}`,
  );
}
