"use client";

import {
  Area,
  AreaChart,
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
import type { PeriodoMetrica } from "@/types";

interface TrendChartProps {
  data: PeriodoMetrica[];
}

export function TrendChart({ data }: TrendChartProps) {
  if (data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Tendencia histórica</CardTitle>
          <CardDescription>
            Evolución del promedio general por período.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex h-[280px] items-center justify-center">
            <p className="text-sm text-muted-foreground">
              No hay datos históricos disponibles.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Tendencia histórica</CardTitle>
        <CardDescription>
          Evolución del promedio general por período.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart
            data={data}
            margin={{ top: 8, right: 8, left: -12, bottom: 0 }}
          >
            <defs>
              <linearGradient id="gradPromedio" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              className="stroke-border"
              vertical={false}
            />
            <XAxis
              dataKey="periodo"
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
                const d = payload[0].payload as PeriodoMetrica;
                return (
                  <div className="rounded-lg border bg-card px-3 py-2 text-sm shadow-md">
                    <p className="font-medium">{d.periodo}</p>
                    <p className="text-muted-foreground">
                      Promedio:{" "}
                      <span className="font-semibold text-foreground">
                        {d.promedio}%
                      </span>
                    </p>
                    <p className="text-muted-foreground">
                      Evaluaciones: {d.evaluaciones_count}
                    </p>
                  </div>
                );
              }}
            />
            <Area
              type="monotone"
              dataKey="promedio"
              stroke="#3b82f6"
              strokeWidth={2}
              fill="url(#gradPromedio)"
              dot={{ r: 4, fill: "#3b82f6", strokeWidth: 0 }}
              activeDot={{ r: 6, fill: "#3b82f6" }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
