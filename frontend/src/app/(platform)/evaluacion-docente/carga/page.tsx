"use client";

import { useState } from "react";
import { UploadPanel } from "@/features/evaluacion-docente/components/upload";
import { RecentUploads } from "@/features/evaluacion-docente/components/upload/recent-uploads";
import { useDocuments } from "@/features/evaluacion-docente/hooks/use-documents";

export default function CargaPage() {
  const { documents, total, isLoading, isEmpty, refetch } = useDocuments({
    page: 1,
    page_size: 10,
    sort_by: "created_at",
    sort_order: "desc",
  });
  const [hidden, setHidden] = useState(false);

  const handleUploadComplete = () => {
    setHidden(false);
    refetch();
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Cargar PDFs</h2>
        <p className="text-muted-foreground">
          Sube archivos PDF de evaluaciones docentes para su procesamiento.
        </p>
      </div>

      <UploadPanel onUploadComplete={handleUploadComplete} />
      {!hidden && (
        <RecentUploads
          documents={documents}
          total={total}
          isLoading={isLoading}
          isEmpty={isEmpty}
          onClear={() => setHidden(true)}
        />
      )}
    </div>
  );
}
