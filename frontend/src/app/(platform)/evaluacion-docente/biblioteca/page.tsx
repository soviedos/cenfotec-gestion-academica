import { DocumentLibrary } from "@/features/evaluacion-docente/components/biblioteca";

export default function BibliotecaPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">
          Biblioteca documental
        </h2>
        <p className="text-muted-foreground">
          Repositorio de evaluaciones docentes procesadas y documentos
          asociados.
        </p>
      </div>

      <DocumentLibrary />
    </div>
  );
}
