"use client";

import { useCallback, useRef, useState } from "react";
import { Upload as UploadIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { DropZone } from "./drop-zone";
import { FileItem, type FileItemData, type FileItemStatus } from "./file-item";
import { uploadDocument, ApiClientError } from "@/features/evaluacion-docente/lib/api/documents";

function nextFileId(): string {
  return crypto.randomUUID();
}

export function UploadPanel() {
  const [files, setFiles] = useState<FileItemData[]>([]);
  const uploadingRef = useRef(false);

  const hasFiles = files.length > 0;
  const pendingCount = files.filter((f) => f.status === "pending").length;
  const successCount = files.filter((f) => f.status === "success").length;
  const errorCount = files.filter((f) => f.status === "error").length;
  const isUploading = files.some((f) => f.status === "uploading");

  const addFiles = useCallback((newFiles: File[]) => {
    setFiles((prev) => {
      const existingNames = new Set(prev.map((f) => f.file.name));
      const unique = newFiles.filter((f) => !existingNames.has(f.name));
      return [
        ...prev,
        ...unique.map((file) => ({
          id: nextFileId(),
          file,
          status: "pending" as FileItemStatus,
        })),
      ];
    });
  }, []);

  const removeFile = useCallback((id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  }, []);

  const updateFileStatus = useCallback(
    (id: string, status: FileItemStatus, error?: string) => {
      setFiles((prev) =>
        prev.map((f) => (f.id === id ? { ...f, status, error } : f)),
      );
    },
    [],
  );

  const uploadAll = useCallback(async () => {
    if (uploadingRef.current) return;
    uploadingRef.current = true;

    const pending = files.filter((f) => f.status === "pending");

    for (const item of pending) {
      updateFileStatus(item.id, "uploading");
      try {
        await uploadDocument(item.file);
        updateFileStatus(item.id, "success");
      } catch (err) {
        const message =
          err instanceof ApiClientError
            ? ((err.body as { detail?: string })?.detail ?? err.message)
            : "Error inesperado al subir el archivo";
        updateFileStatus(item.id, "error", message);
      }
    }

    uploadingRef.current = false;
  }, [files, updateFileStatus]);

  const clearCompleted = useCallback(() => {
    setFiles((prev) => prev.filter((f) => f.status !== "success"));
  }, []);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Subir archivos</CardTitle>
            <CardDescription>
              Arrastra archivos PDF o haz clic para seleccionar. Formatos
              aceptados: PDF.
            </CardDescription>
          </div>
          {hasFiles && (
            <div className="flex items-center gap-2">
              {successCount > 0 && (
                <Badge variant="secondary">{successCount} completados</Badge>
              )}
              {errorCount > 0 && (
                <Badge variant="destructive">{errorCount} con error</Badge>
              )}
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <DropZone onFilesSelected={addFiles} disabled={isUploading} />

        {hasFiles && (
          <>
            <div
              className="space-y-2"
              role="list"
              aria-label="Archivos seleccionados"
            >
              {files.map((item) => (
                <FileItem key={item.id} item={item} onRemove={removeFile} />
              ))}
            </div>

            <div className="flex items-center justify-between border-t pt-4">
              <div className="flex gap-2">
                {successCount > 0 && (
                  <Button variant="outline" size="sm" onClick={clearCompleted}>
                    Limpiar completados
                  </Button>
                )}
              </div>
              <Button
                size="sm"
                onClick={uploadAll}
                disabled={pendingCount === 0 || isUploading}
              >
                <UploadIcon className="mr-1.5 h-4 w-4" />
                {isUploading
                  ? "Subiendo..."
                  : `Subir ${pendingCount} archivo${pendingCount !== 1 ? "s" : ""}`}
              </Button>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
