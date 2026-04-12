"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { temaLabel } from "@/features/evaluacion-docente/lib/business-rules";
import type { TemaDistribucion } from "@/features/evaluacion-docente/types";

interface ThemeBarChartProps {
  data: TemaDistribucion[];
  onThemeClick?: (tema: string) => void;
}

export function ThemeBarChart({ data, onThemeClick }: ThemeBarChartProps) {
  if (data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Temas recurrentes</CardTitle>
          <CardDescription>
            Distribución de comentarios por tema.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex h-80 items-center justify-center">
            <p className="text-sm text-muted-foreground">
              No hay datos de temas disponibles.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const chartData = data
    .map((d) => ({
      name: temaLabel(d.tema),
      raw: d.tema,
      count: d.count,
      porcentaje: d.porcentaje,
    }))
    .sort((a, b) => b.count - a.count);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Temas recurrentes</CardTitle>
        <CardDescription>
          Distribución de comentarios por tema. Clic en una barra para filtrar.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={320}>
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 8, right: 8, left: 8, bottom: 0 }}
            onClick={(e) => {
              const payload = (
                e as unknown as {
                  activePayload?: { payload?: { raw?: string } }[];
                }
              )?.activePayload;
              if (payload?.[0]?.payload?.raw && onThemeClick) {
                onThemeClick(payload[0].payload.raw);
              }
            }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              className="stroke-border"
              horizontal={false}
            />
            <XAxis
              type="number"
              tick={{ fontSize: 11 }}
              className="fill-muted-foreground"
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              type="category"
              dataKey="name"
              width={110}
              tick={{ fontSize: 11 }}
              className="fill-muted-foreground"
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const d = payload[0].payload as (typeof chartData)[0];
                return (
                  <div className="rounded-lg border bg-card px-3 py-2 text-sm shadow-md">
                    <p className="font-medium">{d.name}</p>
                    <p className="text-muted-foreground">
                      Cantidad:{" "}
                      <span className="font-semibold text-foreground">
                        {d.count}
                      </span>
                    </p>
                    <p className="text-muted-foreground">
                      Porcentaje:{" "}
                      <span className="font-semibold text-foreground">
                        {d.porcentaje.toFixed(1)}%
                      </span>
                    </p>
                  </div>
                );
              }}
            />
            <Bar
              dataKey="count"
              radius={[0, 6, 6, 0]}
              className="fill-violet-500 cursor-pointer"
              maxBarSize={32}
            />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
