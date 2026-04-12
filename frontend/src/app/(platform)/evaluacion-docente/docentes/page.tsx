import type { Metadata } from "next";
import { Users } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export const metadata: Metadata = {
  title: "Docentes",
};

export default function DocentesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Docentes</h2>
        <p className="text-muted-foreground">
          Directorio de docentes registrados y sus evaluaciones históricas.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Sin docentes registrados</CardTitle>
          <CardDescription>
            Los docentes se registran automáticamente al procesar evaluaciones.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Users className="mb-4 h-10 w-10 text-muted-foreground/40" />
            <p className="text-sm text-muted-foreground">
              Los docentes aparecerán aquí conforme se procesen evaluaciones.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
