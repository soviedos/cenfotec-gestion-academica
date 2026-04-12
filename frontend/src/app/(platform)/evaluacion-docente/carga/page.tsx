import { UploadPanel } from "@/features/evaluacion-docente/components/upload";

export default function CargaPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Cargar PDFs</h2>
        <p className="text-muted-foreground">
          Sube archivos PDF de evaluaciones docentes para su procesamiento.
        </p>
      </div>

      <UploadPanel />
    </div>
  );
}
