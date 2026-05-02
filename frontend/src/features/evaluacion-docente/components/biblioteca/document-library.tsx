"use client";

import { useCallback, useState } from "react";
import { RefreshCw, Trash2 } from "lucide-react";
import type { RowSelectionState } from "@tanstack/react-table";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { useDocuments } from "@/features/evaluacion-docente/hooks/use-documents";
import {
  deleteDocument,
  bulkDeleteDocuments,
} from "@/features/evaluacion-docente/lib/api/documents";
import type {
  DocumentoFilterParams,
  DocumentoSortField,
} from "@/features/evaluacion-docente/types";
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
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
  const [isBulkDeleting, setIsBulkDeleting] = useState(false);

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

  const selectedCount = Object.keys(rowSelection).length;
  const selectedIds = Object.keys(rowSelection).map(
    (idx) => documents[Number(idx)].id,
  );

  const handleBulkDelete = useCallback(async () => {
    if (selectedIds.length === 0) return;
    setIsBulkDeleting(true);
    try {
      await bulkDeleteDocuments(selectedIds);
      setRowSelection({});
      refetch();
    } finally {
      setIsBulkDeleting(false);
    }
  }, [selectedIds, refetch]);

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

  const handleDelete = useCallback(
    async (id: string) => {
      try {
        await deleteDocument(id);
        refetch();
      } catch {
        // Silently refetch to sync state even on error
        refetch();
      }
    },
    [refetch],
  );

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
              Biblioteca de PDFs de evaluaciones docentes cargados en la
              plataforma.
            </CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={refetch}
            disabled={isLoading}
            aria-label="Recargar documentos"
          >
            <RefreshCw
              className={`mr-1.5 h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`}
            />
            Recargar
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <DocumentFilters
          onFilterChange={handleFilterChange}
          isLoading={isLoading}
        />

        {error && (
          <div
            className="rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive"
            role="alert"
          >
            {error}
          </div>
        )}

        {selectedCount > 0 && (
          <div className="flex items-center gap-3 rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-2">
            <span className="text-sm font-medium">
              {selectedCount} documento{selectedCount > 1 ? "s" : ""}{" "}
              seleccionado{selectedCount > 1 ? "s" : ""}
            </span>
            <AlertDialog>
              <AlertDialogTrigger
                render={
                  <Button
                    variant="destructive"
                    size="sm"
                    disabled={isBulkDeleting}
                    aria-label="Eliminar seleccionados"
                  />
                }
              >
                <Trash2 className="mr-1.5 h-3.5 w-3.5" />
                Eliminar seleccionados
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>
                    ¿Eliminar {selectedCount} documento
                    {selectedCount > 1 ? "s" : ""}?
                  </AlertDialogTitle>
                  <AlertDialogDescription>
                    Se eliminarán permanentemente los documentos seleccionados
                    junto con todas sus evaluaciones, dimensiones, cursos y
                    comentarios asociados. Esta acción no se puede deshacer.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancelar</AlertDialogCancel>
                  <AlertDialogAction
                    onClick={handleBulkDelete}
                    className="bg-destructive text-white hover:bg-destructive/90"
                  >
                    Eliminar {selectedCount}
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        )}

        <DocumentTable
          data={documents}
          isLoading={isLoading}
          isEmpty={isEmpty}
          sortBy={params.sort_by ?? "created_at"}
          sortOrder={params.sort_order ?? "desc"}
          onSort={handleSort}
          onDelete={handleDelete}
          rowSelection={rowSelection}
          onRowSelectionChange={setRowSelection}
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
