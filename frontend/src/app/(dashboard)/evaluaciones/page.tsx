import type { Metadata } from "next";
import { FileText } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export const metadata: Metadata = {
  title: "Evaluaciones",
};

export default function EvaluacionesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Evaluaciones</h2>
        <p className="text-muted-foreground">
          Listado de evaluaciones docentes procesadas.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Sin evaluaciones</CardTitle>
          <CardDescription>
            Aún no se han procesado evaluaciones. Sube PDFs desde la sección de
            carga.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <FileText className="mb-4 h-10 w-10 text-muted-foreground/50" />
            <p className="text-sm text-muted-foreground">
              Las evaluaciones aparecerán aquí una vez procesadas.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
