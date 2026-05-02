"use client";

import { useMemo } from "react";
import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { DimensionPromedio } from "@/features/evaluacion-docente/types";

const RADAR_COLORS = {
  estudiante: "#6366f1",
  director: "#f59e0b",
  autoeval: "#10b981",
  promedio: "#3b82f6",
} as const;

interface DimensionRadarChartProps {
  data: DimensionPromedio[];
}

export function DimensionRadarChart({ data }: DimensionRadarChartProps) {
  if (data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Dimensiones de evaluación</CardTitle>
          <CardDescription>
            Radar por dimensión y fuente evaluativa.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex h-80 items-center justify-center">
            <p className="text-sm text-muted-foreground">
              No hay datos de dimensiones disponibles.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const chartData = data.map((d) => ({
    dimension:
      d.dimension.length > 14 ? d.dimension.slice(0, 12) + "…" : d.dimension,
    fullDimension: d.dimension,
    Estudiante: d.pct_estudiante ?? 0,
    Director: d.pct_director ?? 0,
    Autoeval: d.pct_autoeval ?? 0,
    Promedio: d.pct_promedio ?? 0,
  }));

  // Dynamic domain: floor to nearest 10 below the minimum value so
  // differences between series/filters are visually amplified.
  const domainMin = useMemo(() => {
    const allValues = data.flatMap((d) => [
      d.pct_estudiante ?? 0,
      d.pct_director ?? 0,
      d.pct_autoeval ?? 0,
      d.pct_promedio ?? 0,
    ]);
    const min = Math.min(...allValues);
    return Math.max(0, Math.floor(min / 10) * 10 - 10);
  }, [data]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Dimensiones de evaluación</CardTitle>
        <CardDescription>
          Radar por dimensión y fuente evaluativa.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="mb-3 flex flex-wrap items-center gap-4 text-xs">
          {(
            [
              ["Estudiante", RADAR_COLORS.estudiante],
              ["Director", RADAR_COLORS.director],
              ["Autoeval.", RADAR_COLORS.autoeval],
              ["Promedio", RADAR_COLORS.promedio],
            ] as const
          ).map(([label, color]) => (
            <span key={label} className="flex items-center gap-1.5">
              <span
                className="inline-block size-2.5 rounded-full"
                style={{ backgroundColor: color }}
              />
              {label}
            </span>
          ))}
        </div>
        <ResponsiveContainer width="100%" height={320}>
          <RadarChart data={chartData} cx="50%" cy="50%" outerRadius="75%">
            <PolarGrid
              gridType="polygon"
              stroke="#d1d5db"
              fill="none"
              fillOpacity={0}
            />
            <PolarAngleAxis
              dataKey="dimension"
              tick={{ fontSize: 11 }}
              className="fill-muted-foreground"
            />
            <PolarRadiusAxis
              angle={90}
              domain={[domainMin, 100]}
              tick={{ fontSize: 10 }}
              className="fill-muted-foreground"
            />
            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const d = payload[0].payload as (typeof chartData)[0];
                return (
                  <div className="rounded-lg border bg-card px-3 py-2 text-sm shadow-md">
                    <p className="mb-1 font-medium">{d.fullDimension}</p>
                    <p>
                      Estudiante:{" "}
                      <span className="font-semibold">{d.Estudiante}%</span>
                    </p>
                    <p>
                      Director:{" "}
                      <span className="font-semibold">{d.Director}%</span>
                    </p>
                    <p>
                      Autoeval:{" "}
                      <span className="font-semibold">{d.Autoeval}%</span>
                    </p>
                    <p>
                      Promedio:{" "}
                      <span className="font-semibold">{d.Promedio}%</span>
                    </p>
                  </div>
                );
              }}
            />
            <Radar
              name="Estudiante"
              dataKey="Estudiante"
              stroke={RADAR_COLORS.estudiante}
              fill="none"
              strokeWidth={2}
              isAnimationActive={false}
              dot={{ r: 4, fill: RADAR_COLORS.estudiante, strokeWidth: 0 }}
            />
            <Radar
              name="Director"
              dataKey="Director"
              stroke={RADAR_COLORS.director}
              fill="none"
              strokeWidth={2}
              isAnimationActive={false}
              dot={{ r: 4, fill: RADAR_COLORS.director, strokeWidth: 0 }}
            />
            <Radar
              name="Autoeval"
              dataKey="Autoeval"
              stroke={RADAR_COLORS.autoeval}
              fill="none"
              strokeWidth={2}
              isAnimationActive={false}
              dot={{ r: 4, fill: RADAR_COLORS.autoeval, strokeWidth: 0 }}
            />
            <Radar
              name="Promedio"
              dataKey="Promedio"
              stroke={RADAR_COLORS.promedio}
              fill="none"
              strokeWidth={2.5}
              strokeDasharray="5 3"
              isAnimationActive={false}
              dot={{ r: 4, fill: RADAR_COLORS.promedio, strokeWidth: 0 }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
