"use client";

import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { PieLabelRenderProps } from "recharts";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { SentimientoDistribucion } from "@/types";

const COLORS: Record<string, string> = {
  positivo: "#10b981",
  neutro: "#94a3b8",
  mixto: "#f59e0b",
  negativo: "#ef4444",
};

const LABELS: Record<string, string> = {
  positivo: "Positivo",
  neutro: "Neutro",
  mixto: "Mixto",
  negativo: "Negativo",
};

interface SentimentChartProps {
  data: SentimientoDistribucion[];
}

export function SentimentChart({ data }: SentimentChartProps) {
  if (data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Distribución por sentimiento</CardTitle>
          <CardDescription>
            Proporción de comentarios según polaridad.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex h-[300px] items-center justify-center">
            <p className="text-sm text-muted-foreground">
              No hay datos de sentimiento disponibles.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const chartData = data.map((d) => ({
    name: LABELS[d.sentimiento] ?? d.sentimiento,
    value: d.count,
    porcentaje: d.porcentaje,
    fill: COLORS[d.sentimiento] ?? "#6b7280",
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Distribución por sentimiento</CardTitle>
        <CardDescription>
          Proporción de comentarios según polaridad.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={3}
              dataKey="value"
              nameKey="name"
              label={(props: PieLabelRenderProps) => {
                const name = String(props.name ?? "");
                const percent = Number(props.percent ?? 0);
                return `${name} ${(percent * 100).toFixed(1)}%`;
              }}
              labelLine={false}
            >
              {chartData.map((entry) => (
                <Cell key={entry.name} fill={entry.fill} />
              ))}
            </Pie>
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
                        {d.value}
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
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
