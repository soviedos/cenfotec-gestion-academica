import type { Metadata } from "next";
import { QualitativeDashboard } from "@/features/evaluacion-docente/components/sentimiento";

export const metadata: Metadata = {
  title: "Análisis de sentimiento",
};

export default function SentimientoPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">
          Análisis de sentimiento
        </h2>
        <p className="text-muted-foreground">
          Percepción cualitativa extraída de los comentarios en las
          evaluaciones.
        </p>
      </div>

      <QualitativeDashboard />
    </div>
  );
}
