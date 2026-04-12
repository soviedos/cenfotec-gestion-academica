import { apiClient } from "@/lib/api-client";
import type { QueryRequest, QueryResponse } from "@/features/evaluacion-docente/types";

export async function postQuery(
  body: QueryRequest,
  signal?: AbortSignal,
): Promise<QueryResponse> {
  return apiClient.post<QueryResponse>("/api/v1/query", body, signal);
}
