"use client";

import { useCallback, useState } from "react";
import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useDocuments } from "@/hooks/use-documents";
import type { DocumentoFilterParams, DocumentoSortField } from "@/types";
import { DocumentFilters, type FilterValues } from "./document-filters";
import { DocumentTable } from "./document-table";
import { PaginationBar } from "./pagination-bar";

export function DocumentLibrary() {
  const [params, setParams] = useState<DocumentoFilterParams>({
    page: 1,
    page_size: 20,
    sort_by: "created_at",
    sort_order: "desc",
  });

  const {
    documents,
    total,
    totalPages,
    page,
    pageSize,
    isLoading,
    error,
    isEmpty,
    refetch,
  } = useDocuments(params);

  const handleFilterChange = useCallback((filters: FilterValues) => {
    setParams((prev) => ({
      ...prev,
      page: 1, // reset to first page on filter change
      nombre_archivo: filters.nombre_archivo || undefined,
      docente: filters.docente || undefined,
      periodo: filters.periodo || undefined,
      estado: filters.estado || undefined,
    }));
  }, []);

  const handleSort = useCallback((field: string) => {
    setParams((prev) => ({
      ...prev,
      page: 1,
      sort_by: field as DocumentoSortField,
      sort_order:
        prev.sort_by === field && prev.sort_order === "desc" ? "asc" : "desc",
    }));
  }, []);

  const handlePageChange = useCallback((newPage: number) => {
    setParams((prev) => ({ ...prev, page: newPage }));
  }, []);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              Documentos
              {!isLoading && (
                <Badge variant="secondary" className="font-normal">
                  {total}
                </Badge>
              )}
            </CardTitle>
            <CardDescription>
              Biblioteca de PDFs de evaluaciones docentes cargados en la plataforma.
            </CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={refetch}
            disabled={isLoading}
            aria-label="Recargar documentos"
          >
            <RefreshCw className={`mr-1.5 h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />
            Recargar
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <DocumentFilters onFilterChange={handleFilterChange} isLoading={isLoading} />

        {error && (
          <div
            className="rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive"
            role="alert"
          >
            {error}
          </div>
        )}

        <DocumentTable
          data={documents}
          isLoading={isLoading}
          isEmpty={isEmpty}
          sortBy={params.sort_by ?? "created_at"}
          sortOrder={params.sort_order ?? "desc"}
          onSort={handleSort}
        />

        <PaginationBar
          page={page}
          pageSize={pageSize}
          total={total}
          totalPages={totalPages}
          onPageChange={handlePageChange}
          isLoading={isLoading}
        />
      </CardContent>
    </Card>
  );
}
