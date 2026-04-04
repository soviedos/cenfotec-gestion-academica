import type { Metadata } from "next";
import { AnalyticsDashboard } from "@/components/dashboard";

export const metadata: Metadata = {
  title: "Análisis estadístico",
};

export default function EstadisticasPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">
          Análisis estadístico
        </h2>
        <p className="text-muted-foreground">
          Métricas cuantitativas, tendencias y distribuciones de puntajes.
        </p>
      </div>

      <AnalyticsDashboard />
    </div>
  );
}
