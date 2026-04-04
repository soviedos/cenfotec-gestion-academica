"use client";

import { useState, useEffect } from "react";
import {
  MessageSquare,
  ThumbsUp,
  ThumbsDown,
  TrendingUp,
} from "lucide-react";
import { useQualitative } from "@/hooks/use-qualitative";
import type { QualitativeFilters } from "@/hooks/use-qualitative";
import { fetchFiltrosCualitativos } from "@/lib/api/qualitative";
import type { FiltrosCualitativos } from "@/types";
import { KpiCard } from "@/components/dashboard/kpi-card";
import { SentimentChart } from "@/components/sentimiento/sentiment-chart";
import { ThemeBarChart } from "@/components/sentimiento/theme-bar-chart";
import { CommentTable } from "@/components/sentimiento/comment-table";
import { QualitativeFilterBar } from "@/components/sentimiento/qualitative-filter-bar";
import {
  QualitativeSkeleton,
  QualitativeEmpty,
  QualitativeError,
} from "@/components/sentimiento/qualitative-states";

export function QualitativeDashboard() {
  const [filters, setFilters] = useState<QualitativeFilters>({});
  const [filterOptions, setFilterOptions] = useState<FiltrosCualitativos>({
    periodos: [],
    docentes: [],
    asignaturas: [],
    escuelas: [],
  });

  useEffect(() => {
    fetchFiltrosCualitativos().then(setFilterOptions).catch(() => {});
  }, []);

  const { resumen, comentarios, temas, sentimientos, isLoading, error, isEmpty, refetch } =
    useQualitative(filters);

  const updateFilter = <K extends keyof QualitativeFilters>(
    key: K,
    value: QualitativeFilters[K],
  ) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const clearFilters = () => setFilters({});

  if (isLoading && !resumen) {
    return <QualitativeSkeleton />;
  }

  if (error) {
    return <QualitativeError message={error} onRetry={refetch} />;
  }

  if (isEmpty) {
    return <QualitativeEmpty />;
  }

  // Compute KPI values from resumen
  const totalComentarios = resumen?.total_comentarios ?? 0;
  const positivos =
    resumen?.por_sentimiento.find((s) => s.sentimiento === "positivo")?.count ?? 0;
  const negativos =
    resumen?.por_sentimiento.find((s) => s.sentimiento === "negativo")?.count ?? 0;
  const sentimientoPromedio = resumen?.sentimiento_promedio;

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          label="Total comentarios"
          value={totalComentarios}
          icon={MessageSquare}
          description="Comentarios analizados"
        />
        <KpiCard
          label="Positivos"
          value={positivos}
          icon={ThumbsUp}
          description={
            totalComentarios > 0
              ? `${((positivos / totalComentarios) * 100).toFixed(1)}% del total`
              : "Sin datos"
          }
        />
        <KpiCard
          label="Negativos"
          value={negativos}
          icon={ThumbsDown}
          description={
            totalComentarios > 0
              ? `${((negativos / totalComentarios) * 100).toFixed(1)}% del total`
              : "Sin datos"
          }
        />
        <KpiCard
          label="Score promedio"
          value={
            sentimientoPromedio !== null && sentimientoPromedio !== undefined
              ? `${(sentimientoPromedio * 100).toFixed(0)}%`
              : "—"
          }
          icon={TrendingUp}
          description="Índice de positividad"
        />
      </div>

      {/* Filters */}
      <QualitativeFilterBar
        periodo={filters.periodo}
        docente={filters.docente}
        asignatura={filters.asignatura}
        escuela={filters.escuela}
        tipo={filters.tipo}
        tema={filters.tema}
        sentimiento={filters.sentimiento}
        periodos={filterOptions.periodos}
        docentes={filterOptions.docentes}
        asignaturas={filterOptions.asignaturas}
        escuelas={filterOptions.escuelas}
        onPeriodoChange={(v) => updateFilter("periodo", v)}
        onDocenteChange={(v) => updateFilter("docente", v)}
        onAsignaturaChange={(v) => updateFilter("asignatura", v)}
        onEscuelaChange={(v) => updateFilter("escuela", v)}
        onTipoChange={(v) => updateFilter("tipo", v)}
        onTemaChange={(v) => updateFilter("tema", v)}
        onSentimientoChange={(v) => updateFilter("sentimiento", v)}
        onClear={clearFilters}
      />

      {/* Charts row */}
      <div className="grid gap-6 lg:grid-cols-2">
        <SentimentChart data={sentimientos} />
        <ThemeBarChart
          data={temas}
          onThemeClick={(tema) => updateFilter("tema", tema)}
        />
      </div>

      {/* Comment table */}
      <CommentTable
        data={comentarios}
        onTemaClick={(tema) => updateFilter("tema", tema)}
        onSentimientoClick={(s) => updateFilter("sentimiento", s)}
      />
    </div>
  );
}
