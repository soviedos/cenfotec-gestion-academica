"use client";

import { listDocuments } from "@/features/evaluacion-docente/lib/api/documents";
import type {
  Documento,
  DocumentoFilterParams,
  PaginatedResponse,
} from "@/features/evaluacion-docente/types";
import { useApiFetch } from "@/hooks/use-api-fetch";

export function useDocuments(params: DocumentoFilterParams = {}) {
  const paramsKey = JSON.stringify(params);

  const { data, isLoading, error, refetch } = useApiFetch<
    PaginatedResponse<Documento>
  >(
    (signal) => listDocuments(params, signal),
    [paramsKey],
    "Error al cargar documentos",
  );

  return {
    documents: data?.items ?? [],
    total: data?.total ?? 0,
    totalPages: data?.total_pages ?? 1,
    page: data?.page ?? params.page ?? 1,
    pageSize: data?.page_size ?? params.page_size ?? 20,
    isLoading,
    error,
    isEmpty: !isLoading && (data?.items.length ?? 0) === 0,
    refetch,
  };
}
