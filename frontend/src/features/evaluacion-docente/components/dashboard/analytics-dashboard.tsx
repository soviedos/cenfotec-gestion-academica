"use client";

import { useState, useEffect } from "react";
import { BarChart3, GraduationCap, TrendingUp, Users } from "lucide-react";
import { useAnalytics } from "@/features/evaluacion-docente/hooks/use-analytics";
import {
  fetchPeriodos,
  fetchEscuelas,
  fetchCursos,
} from "@/features/evaluacion-docente/lib/api/analytics";
import { KpiCard } from "@/features/evaluacion-docente/components/dashboard/kpi-card";
import { DocenteBarChart } from "@/features/evaluacion-docente/components/dashboard/docente-bar-chart";
import { DimensionRadarChart } from "@/features/evaluacion-docente/components/dashboard/dimension-radar-chart";
import { TrendChart } from "@/features/evaluacion-docente/components/dashboard/trend-chart";
import { RankingTable } from "@/features/evaluacion-docente/components/dashboard/ranking-table";
import { PeriodFilter } from "@/features/evaluacion-docente/components/dashboard/period-filter";
import {
  DashboardSkeleton,
  DashboardEmpty,
  DashboardError,
} from "@/features/evaluacion-docente/components/dashboard/dashboard-states";
import type {
  Modalidad,
  PeriodoOption,
} from "@/features/evaluacion-docente/types";

export function AnalyticsDashboard() {
  const [modalidad, setModalidad] = useState<Modalidad | undefined>();
  const [periodo, setPeriodo] = useState<string | undefined>();
  const [escuela, setEscuela] = useState<string | undefined>();
  const [curso, setCurso] = useState<string | undefined>();
  const [escuelas, setEscuelas] = useState<string[]>([]);
  const [cursos, setCursos] = useState<string[]>([]);
  const [periodos, setPeriodos] = useState<PeriodoOption[]>([]);

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

  // Fetch all periodos once on mount (independent of modalidad filter)
  useEffect(() => {
    const controller = new AbortController();
    fetchPeriodos({}, controller.signal)
      .then(setPeriodos)
      .catch(() => {});
    return () => controller.abort();
  }, []);

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
