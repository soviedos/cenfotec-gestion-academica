import { apiClient, ApiClientError } from "@/lib/api-client";
import { buildQuery } from "@/features/evaluacion-docente/lib/api/query-builder";
import type {
  Documento,
  DocumentoFilterParams,
  DocumentoUploadResponse,
  DuplicadoRead,
  PaginatedResponse,
} from "@/features/evaluacion-docente/types";

export async function uploadDocument(
  file: File,
): Promise<DocumentoUploadResponse> {
  return apiClient.upload<DocumentoUploadResponse>(
    "/api/v1/documentos/upload",
    file,
  );
}

export async function listDocuments(
  params: DocumentoFilterParams = {},
  signal?: AbortSignal,
): Promise<PaginatedResponse<Documento>> {
  const endpoint = `/api/v1/documentos/${buildQuery(params)}`;
  return apiClient.get<PaginatedResponse<Documento>>(endpoint, signal);
}

export async function listPeriodos(): Promise<string[]> {
  return apiClient.get<string[]>("/api/v1/documentos/periodos");
}

export async function deleteDocument(id: string): Promise<void> {
  await apiClient.delete(`/api/v1/documentos/${id}`);
}

export async function listDuplicados(
  documentoId: string,
): Promise<DuplicadoRead[]> {
  return apiClient.get<DuplicadoRead[]>(
    `/api/v1/documentos/${documentoId}/duplicados`,
  );
}

export function getDocumentDownloadUrl(id: string): string {
  return `/api/v1/documentos/${id}/download`;
}

export { ApiClientError };
