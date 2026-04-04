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
import type { DocentePromedio } from "@/types";

interface DocenteBarChartProps {
  data: DocentePromedio[];
}

export function DocenteBarChart({ data }: DocenteBarChartProps) {
  if (data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Promedio por docente</CardTitle>
          <CardDescription>
            Comparativa de puntaje general por docente.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <EmptyState message="No hay datos de docentes disponibles." />
        </CardContent>
      </Card>
    );
  }

  const chartData = data.map((d) => ({
    name:
      d.docente_nombre.length > 18
        ? d.docente_nombre.slice(0, 16) + "…"
        : d.docente_nombre,
    fullName: d.docente_nombre,
    promedio: d.promedio,
    evaluaciones: d.evaluaciones_count,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Promedio por docente</CardTitle>
        <CardDescription>
          Comparativa de puntaje general por docente.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={320}>
          <BarChart
            data={chartData}
            margin={{ top: 8, right: 8, left: -12, bottom: 0 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              className="stroke-border"
              vertical={false}
            />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 11 }}
              className="fill-muted-foreground"
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              domain={[0, 100]}
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
                    <p className="font-medium">{d.fullName}</p>
                    <p className="text-muted-foreground">
                      Promedio:{" "}
                      <span className="font-semibold text-foreground">
                        {d.promedio}%
                      </span>
                    </p>
                    <p className="text-muted-foreground">
                      Evaluaciones: {d.evaluaciones}
                    </p>
                  </div>
                );
              }}
            />
            <Bar
              dataKey="promedio"
              radius={[6, 6, 0, 0]}
              className="fill-primary"
              maxBarSize={48}
            />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex h-[320px] items-center justify-center">
      <p className="text-sm text-muted-foreground">{message}</p>
    </div>
  );
}
