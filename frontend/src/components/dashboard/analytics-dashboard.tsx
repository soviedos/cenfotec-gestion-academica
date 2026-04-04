"use client";

import { useState, useMemo } from "react";
import {
  BarChart3,
  GraduationCap,
  TrendingUp,
  Users,
} from "lucide-react";
import { useAnalytics } from "@/hooks/use-analytics";
import { KpiCard } from "@/components/dashboard/kpi-card";
import { DocenteBarChart } from "@/components/dashboard/docente-bar-chart";
import { DimensionRadarChart } from "@/components/dashboard/dimension-radar-chart";
import { TrendChart } from "@/components/dashboard/trend-chart";
import { RankingTable } from "@/components/dashboard/ranking-table";
import { PeriodFilter } from "@/components/dashboard/period-filter";
import {
  DashboardSkeleton,
  DashboardEmpty,
  DashboardError,
} from "@/components/dashboard/dashboard-states";

export function AnalyticsDashboard() {
  const [periodo, setPeriodo] = useState<string | undefined>();
  const { resumen, docentes, dimensiones, evolucion, ranking, isLoading, error, isEmpty, refetch } =
    useAnalytics({ periodo });

  const periodos = useMemo(
    () => evolucion.map((e) => e.periodo),
    [evolucion],
  );

  if (isLoading && !resumen) {
    return <DashboardSkeleton />;
  }

  if (error) {
    return <DashboardError message={error} onRetry={refetch} />;
  }

  if (isEmpty) {
    return <DashboardEmpty />;
  }

  return (
    <div className="space-y-6">
      {/* Filters */}
      <PeriodFilter
        periodos={periodos}
        selected={periodo}
        onChange={setPeriodo}
      />

      {/* KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          label="Promedio global"
          value={`${resumen?.promedio_global ?? 0}%`}
          icon={TrendingUp}
          description="Puntaje general promedio"
        />
        <KpiCard
          label="Evaluaciones"
          value={resumen?.total_evaluaciones ?? 0}
          icon={BarChart3}
          description="Evaluaciones procesadas"
        />
        <KpiCard
          label="Docentes"
          value={resumen?.total_docentes ?? 0}
          icon={Users}
          description="Docentes evaluados"
        />
        <KpiCard
          label="Períodos"
          value={resumen?.total_periodos ?? 0}
          icon={GraduationCap}
          description="Períodos académicos"
        />
      </div>

      {/* Charts row 1 */}
      <div className="grid gap-6 lg:grid-cols-2">
        <DocenteBarChart data={docentes} />
        <DimensionRadarChart data={dimensiones} />
      </div>

      {/* Charts row 2 */}
      <div className="grid gap-6 lg:grid-cols-2">
        <TrendChart data={evolucion} />
        <RankingTable data={ranking} />
      </div>
    </div>
  );
}
