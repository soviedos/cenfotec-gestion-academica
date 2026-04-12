"use client";

import { useState, useMemo, useEffect } from "react";
import { BarChart3, GraduationCap, TrendingUp, Users } from "lucide-react";
import { useAnalytics } from "@/hooks/use-analytics";
import { fetchEscuelas, fetchCursos } from "@/lib/api/analytics";
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
import type { Modalidad } from "@/types";

export function AnalyticsDashboard() {
  const [modalidad, setModalidad] = useState<Modalidad | undefined>();
  const [periodo, setPeriodo] = useState<string | undefined>();
  const [escuela, setEscuela] = useState<string | undefined>();
  const [curso, setCurso] = useState<string | undefined>();
  const [escuelas, setEscuelas] = useState<string[]>([]);
  const [cursos, setCursos] = useState<string[]>([]);

  const {
    resumen,
    docentes,
    dimensiones,
    evolucion,
    ranking,
    isLoading,
    error,
    isEmpty,
    refetch,
  } = useAnalytics({ periodo, modalidad, escuela, curso });

  // Fetch escuelas when modalidad/periodo change
  useEffect(() => {
    const controller = new AbortController();
    fetchEscuelas({ modalidad, periodo }, controller.signal)
      .then(setEscuelas)
      .catch(() => {});
    return () => controller.abort();
  }, [modalidad, periodo]);

  // Fetch cursos when escuela/modalidad/periodo change
  useEffect(() => {
    const controller = new AbortController();
    fetchCursos({ escuela, modalidad, periodo }, controller.signal)
      .then(setCursos)
      .catch(() => {});
    return () => controller.abort();
  }, [escuela, modalidad, periodo]);

  // Reset curso when escuela changes
  const handleEscuelaChange = (v: string | undefined) => {
    setEscuela(v);
    setCurso(undefined);
  };

  const periodos = useMemo(
    () =>
      evolucion.map((e) => ({
        periodo: e.periodo,
        modalidad: e.modalidad ?? "",
        año: e.año,
        periodo_orden: e.periodo_orden,
      })),
    [evolucion],
  );

  if (isLoading && !resumen) {
    return <DashboardSkeleton />;
  }

  if (error) {
    return <DashboardError message={error} onRetry={refetch} />;
  }

  if (isEmpty) {
    return (
      <div className="space-y-6">
        <PeriodFilter
          periodos={periodos}
          selectedModalidad={modalidad}
          selectedPeriodo={periodo}
          escuelas={escuelas}
          cursos={cursos}
          selectedEscuela={escuela}
          selectedCurso={curso}
          onModalidadChange={setModalidad}
          onPeriodoChange={setPeriodo}
          onEscuelaChange={handleEscuelaChange}
          onCursoChange={setCurso}
        />
        <DashboardEmpty />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Filters */}
      <PeriodFilter
        periodos={periodos}
        selectedModalidad={modalidad}
        selectedPeriodo={periodo}
        escuelas={escuelas}
        cursos={cursos}
        selectedEscuela={escuela}
        selectedCurso={curso}
        onModalidadChange={setModalidad}
        onPeriodoChange={setPeriodo}
        onEscuelaChange={handleEscuelaChange}
        onCursoChange={setCurso}
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
