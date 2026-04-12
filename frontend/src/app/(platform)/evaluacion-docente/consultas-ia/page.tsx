import type { Metadata } from "next";
import { QueryDashboard } from "@/features/evaluacion-docente/components/consultas-ia";

export const metadata: Metadata = {
  title: "Consultas IA",
};

export default function ConsultasIaPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Consultas IA</h2>
        <p className="text-muted-foreground">
          Realiza preguntas en lenguaje natural sobre las evaluaciones docentes.
        </p>
      </div>

      <QueryDashboard />
    </div>
  );
}
