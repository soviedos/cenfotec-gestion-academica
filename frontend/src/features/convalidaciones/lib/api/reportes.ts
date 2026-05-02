import { apiClient } from "@/lib/api-client";
import { buildQuery } from "@/lib/query-builder";
import type {
  AntecedenteFilterParams,
  AntecedenteHistorico,
  PaginatedResponse,
  ReporteFinal,
} from "@/features/convalidaciones/types";

const BASE = "/api/v1/convalidaciones";

// ── Listado y detalle ────────────────────────────────────────────────

export async function listReportes(
  casoId: string,
  signal?: AbortSignal,
): Promise<ReporteFinal[]> {
  return apiClient.get<ReporteFinal[]>(
    `${BASE}/casos/${casoId}/reportes`,
    signal,
  );
}

export async function fetchReporte(
  casoId: string,
  reporteId: string,
  signal?: AbortSignal,
): Promise<ReporteFinal> {
  return apiClient.get<ReporteFinal>(
    `${BASE}/casos/${casoId}/reportes/${reporteId}`,
    signal,
  );
}

// ── Descarga del PDF ─────────────────────────────────────────────────

/**
 * Retorna la URL firmada (o pública) para descargar el PDF del reporte.
 * Se usa cuando solo se necesita el href de un <a> o window.open().
 */
export function getReporteDownloadUrl(
  casoId: string,
  reporteId?: string,
): string {
  if (reporteId) {
    return `${BASE}/casos/${casoId}/reportes/${reporteId}/download`;
  }
  // Sin reporteId descarga el reporte vigente del caso
  return `${BASE}/casos/${casoId}/reporte/download`;
}

/**
 * Descarga el PDF como Blob.
 * Útil para abrir en una pestaña nueva con object URL o para guardar.
 */
export async function fetchReportePdfBlob(
  casoId: string,
  reporteId?: string,
): Promise<Blob> {
  const url = getReporteDownloadUrl(casoId, reporteId);
  // El apiClient usa JSON por defecto; para Blob hacemos fetch directo
  const { getToken } = await import("@/features/auth/lib/authApi");
  const token = getToken();
  const response = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) {
    throw new Error(`Error al descargar el reporte: ${response.status}`);
  }
  return response.blob();
}

// ── Antecedentes históricos ──────────────────────────────────────────

/**
 * Busca convalidaciones resueltas anteriores similares al caso en curso.
 * Permite apoyar la decisión con precedentes institucionales.
 */
export async function buscarAntecedentes(
  params: AntecedenteFilterParams = {},
  signal?: AbortSignal,
): Promise<PaginatedResponse<AntecedenteHistorico>> {
  return apiClient.get<PaginatedResponse<AntecedenteHistorico>>(
    `${BASE}/antecedentes${buildQuery(params)}`,
    signal,
  );
}

/**
 * Retorna la URL para descargar el PDF asociado a un antecedente histórico.
 */
export function getAntecedenteDownloadUrl(antecedenteId: string): string {
  return `${BASE}/antecedentes/${antecedenteId}/download`;
}
