import type { Metadata } from "next";
import { CommandCenter } from "@/features/evaluacion-docente/components/dashboard/command-center";

export const metadata: Metadata = {
  title: "Centro de control — Evaluaciones Docentes",
};

export default function InicioPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Centro de control</h2>
        <p className="text-muted-foreground">
          Monitoreo en tiempo real de evaluaciones, alertas y métricas docentes.
        </p>
      </div>

      <CommandCenter />
    </div>
  );
}
