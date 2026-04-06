import { apiClient, ApiClientError } from "@/lib/api-client";
import type {
  Documento,
  DocumentoFilterParams,
  DocumentoUploadResponse,
  PaginatedResponse,
} from "@/types";

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
): Promise<PaginatedResponse<Documento>> {
  const searchParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      searchParams.set(key, String(value));
    }
  }
  const query = searchParams.toString();
  const endpoint = `/api/v1/documentos/${query ? `?${query}` : ""}`;
  return apiClient.get<PaginatedResponse<Documento>>(endpoint);
}

export async function listPeriodos(): Promise<string[]> {
  return apiClient.get<string[]>("/api/v1/documentos/periodos");
}

export async function deleteDocument(id: string): Promise<void> {
  await apiClient.delete(`/api/v1/documentos/${id}`);
}

export function getDocumentDownloadUrl(id: string): string {
  return `/api/v1/documentos/${id}/download`;
}

export { ApiClientError };
