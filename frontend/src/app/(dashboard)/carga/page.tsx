import type { Metadata } from "next";
import { Upload } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export const metadata: Metadata = {
  title: "Cargar PDFs",
};

export default function CargaPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Cargar PDFs</h2>
        <p className="text-muted-foreground">
          Sube archivos PDF de evaluaciones docentes para su procesamiento.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Subir archivos</CardTitle>
          <CardDescription>
            Arrastra archivos PDF o haz clic para seleccionar. Formatos
            aceptados: PDF.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-muted-foreground/25 p-12 text-center">
            <Upload className="mb-4 h-10 w-10 text-muted-foreground/50" />
            <p className="text-sm text-muted-foreground">
              Arrastra archivos PDF aquí o haz clic para seleccionar
            </p>
            <p className="mt-1 text-xs text-muted-foreground/70">
              Máximo 50 MB por archivo
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
