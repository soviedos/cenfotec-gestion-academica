"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { listDocuments } from "@/lib/api/documents";
import type {
  Documento,
  DocumentoFilterParams,
  PaginatedResponse,
} from "@/types";

interface UseDocumentsState {
  data: PaginatedResponse<Documento> | null;
  isLoading: boolean;
  error: string | null;
}

const EMPTY_RESPONSE: PaginatedResponse<Documento> = {
  items: [],
  total: 0,
  page: 1,
  page_size: 20,
  total_pages: 1,
};

export function useDocuments(params: DocumentoFilterParams = {}) {
  const [state, setState] = useState<UseDocumentsState>({
    data: null,
    isLoading: true,
    error: null,
  });

  const paramsKey = JSON.stringify(params);
  const abortRef = useRef<AbortController | null>(null);
  const paramsRef = useRef(params);
  paramsRef.current = params;

  const fetchDocuments = useCallback(async () => {
    abortRef.current?.abort();
    abortRef.current = new AbortController();

    setState((prev) => ({ ...prev, isLoading: true, error: null }));

    try {
      const result = await listDocuments(paramsRef.current);
      setState({ data: result, isLoading: false, error: null });
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      const message =
        err instanceof Error ? err.message : "Error al cargar documentos";
      setState((prev) => ({ ...prev, isLoading: false, error: message }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paramsKey]);

  useEffect(() => {
    fetchDocuments();
    return () => abortRef.current?.abort();
  }, [fetchDocuments]);

  return {
    documents: state.data?.items ?? [],
    total: state.data?.total ?? 0,
    totalPages: state.data?.total_pages ?? 1,
    page: state.data?.page ?? params.page ?? 1,
    pageSize: state.data?.page_size ?? params.page_size ?? 20,
    isLoading: state.isLoading,
    error: state.error,
    isEmpty: !state.isLoading && (state.data?.items.length ?? 0) === 0,
    refetch: fetchDocuments,
  };
}
