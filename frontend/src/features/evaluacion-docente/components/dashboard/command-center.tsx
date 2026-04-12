"use client";

import Link from "next/link";
import {
  FileText,
  Users,
  TrendingUp,
  AlertTriangle,
  Upload,
  Library,
  BarChart3,
  Sparkles,
  Clock,
  Lightbulb,
  ArrowDown,
  CheckCircle2,
  XCircle,
  Loader2,
  Trophy,
  ShieldAlert,
  Activity,
  Filter,
} from "lucide-react";
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
import { Badge } from "@/components/ui/badge";
import { useCommandCenter } from "@/features/evaluacion-docente/hooks/use-command-center";
import {
  DashboardSkeleton,
  DashboardEmpty,
  DashboardError,
} from "@/features/evaluacion-docente/components/dashboard/dashboard-states";
import type {
  AlertaResponse,
  AlertaSummary,
  DocenteResumen,
  InsightItem,
  ActividadReciente,
  PeriodoMetrica,
  Modalidad,
  Severidad,
  TipoAlerta,
} from "@/features/evaluacion-docente/types";
import {
  MODALIDADES,
  severidadClasses,
  tipoAlertaLabel,
} from "@/features/evaluacion-docente/lib/business-rules";

// ── Modalidad Selector [BR-MOD-05, BR-FE-20] ───────────────────

function ModalidadSelector({
  value,
  onChange,
}: {
  value: Modalidad | null;
  onChange: (m: Modalidad | null) => void;
}) {
  return (
    <div
      className="flex items-center gap-2"
      role="tablist"
      aria-label="Filtro de modalidad"
    >
      <Filter className="size-4 text-muted-foreground" />
      <div className="flex gap-1 rounded-lg border bg-muted/50 p-0.5">
        <button
          role="tab"
          aria-selected={value === null}
          onClick={() => onChange(null)}
          className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
            value === null
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          Todas
        </button>
        {MODALIDADES.map((m) => (
          <button
            key={m.value}
            role="tab"
            aria-selected={value === m.value}
            onClick={() => onChange(m.value)}
            className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              value === m.value
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {m.label}
          </button>
        ))}
      </div>
    </div>
  );
}

// ── KPI Cards [VZ-01] ──────────────────────────────────────────

function KpiCard({
  label,
  value,
  icon: Icon,
  accent,
  description,
}: {
  label: string;
  value: string | number;
  icon: React.ElementType;
  accent?: string;
  description?: string;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardDescription className="text-sm font-medium">
          {label}
        </CardDescription>
        <Icon className={`size-4 ${accent ?? "text-muted-foreground"}`} />
      </CardHeader>
      <CardContent>
        <p className="text-2xl font-bold">{value}</p>
        {description && (
          <p className="mt-1 text-xs text-muted-foreground">{description}</p>
        )}
      </CardContent>
    </Card>
  );
}

// ── Alert Summary Mini-Cards ────────────────────────────────────

function AlertSummaryBar({ summary }: { summary: AlertaSummary }) {
  const alta = summary.por_severidad.alta ?? 0;
  const media = summary.por_severidad.media ?? 0;
  const baja = summary.por_severidad.baja ?? 0;

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <ShieldAlert className="size-4 text-red-500" />
          Resumen de alertas
        </CardTitle>
        <CardDescription>
          {summary.total_activas} activa{summary.total_activas !== 1 ? "s" : ""}{" "}
          · {summary.docentes_afectados} docente
          {summary.docentes_afectados !== 1 ? "s" : ""} afectado
          {summary.docentes_afectados !== 1 ? "s" : ""}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-3">
          <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-3 text-center">
            <p className="text-2xl font-bold text-red-600">{alta}</p>
            <p className="text-xs text-muted-foreground">Alta</p>
          </div>
          <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3 text-center">
            <p className="text-2xl font-bold text-amber-600">{media}</p>
            <p className="text-xs text-muted-foreground">Media</p>
          </div>
          <div className="rounded-lg border bg-muted/30 p-3 text-center">
            <p className="text-2xl font-bold text-muted-foreground">{baja}</p>
            <p className="text-xs text-muted-foreground">Baja</p>
          </div>
        </div>

        {/* Distribution by type */}
        {Object.keys(summary.por_tipo).length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {Object.entries(summary.por_tipo).map(([tipo, count]) => (
              <Badge key={tipo} variant="outline" className="text-xs">
                {tipoAlertaLabel(tipo as TipoAlerta)}: {count}
              </Badge>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ── Critical Alerts Panel [AL-01, BR-FE-20] ────────────────────

function CriticalAlertsPanel({ alerts }: { alerts: AlertaResponse[] }) {
  if (alerts.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <AlertTriangle className="size-4 text-amber-500" />
            Alertas críticas
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center gap-2 py-6 text-center">
            <CheckCircle2 className="size-8 text-emerald-500" />
            <p className="text-sm text-muted-foreground">
              No hay alertas críticas activas.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <AlertTriangle className="size-4 text-red-500" />
          Alertas críticas ({alerts.length})
        </CardTitle>
        <CardDescription>
          Ordenadas por puntaje más bajo primero
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={`flex items-start justify-between gap-3 rounded-lg border px-3 py-2.5 ${severidadClasses(alert.severidad)}`}
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <p className="truncate text-sm font-medium">
                    {alert.docente_nombre}
                  </p>
                  <Badge variant="outline" className="shrink-0 text-[10px]">
                    {tipoAlertaLabel(alert.tipo_alerta)}
                  </Badge>
                </div>
                <p className="mt-0.5 truncate text-xs text-muted-foreground">
                  {alert.curso} · {alert.periodo}
                </p>
                <p className="mt-0.5 text-xs">{alert.descripcion}</p>
              </div>
              <div className="shrink-0 text-right">
                <p className="text-lg font-bold tabular-nums">
                  {alert.valor_actual.toFixed(1)}%
                </p>
                {alert.valor_anterior != null && (
                  <p className="text-[10px] text-muted-foreground">
                    ant: {alert.valor_anterior.toFixed(1)}%
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// ── Trend Chart [VZ-20, BR-MOD-01] ─────────────────────────────

function TendenciaChart({ data }: { data: PeriodoMetrica[] }) {
  if (data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Activity className="size-4 text-blue-500" />
            Tendencia por período
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex h-52 items-center justify-center">
            <p className="text-sm text-muted-foreground">
              Sin datos históricos.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Activity className="size-4 text-blue-500" />
          Tendencia por período
        </CardTitle>
        <CardDescription>
          Evolución cronológica del promedio general
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart
            data={data}
            margin={{ top: 4, right: 8, left: -12, bottom: 0 }}
          >
            <defs>
              <linearGradient id="gradCC" x1="0" y1="0" x2="0" y2="1">
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
              fill="url(#gradCC)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

// ── Top / Bottom Docentes [BR-FE-22] ───────────────────────────

const MEDAL_COLORS = ["text-amber-500", "text-slate-400", "text-orange-600"];

function DocenteList({
  title,
  icon: Icon,
  docentes,
  variant,
}: {
  title: string;
  icon: React.ElementType;
  docentes: DocenteResumen[];
  variant: "top" | "bottom";
}) {
  if (docentes.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Icon
              className={`size-4 ${variant === "top" ? "text-amber-500" : "text-red-500"}`}
            />
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Sin datos disponibles.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Icon
            className={`size-4 ${variant === "top" ? "text-amber-500" : "text-red-500"}`}
          />
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {docentes.map((d, i) => (
            <div key={d.docente_nombre} className="flex items-center gap-3">
              <span
                className={`flex size-6 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                  variant === "top" && i < 3
                    ? `${MEDAL_COLORS[i]} bg-current/10`
                    : "text-muted-foreground bg-muted"
                }`}
              >
                {d.posicion}
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">
                  {d.docente_nombre}
                </p>
                <p className="text-xs text-muted-foreground">
                  {d.evaluaciones_count} eval.
                </p>
              </div>
              <Badge
                variant={variant === "top" ? "secondary" : "destructive"}
                className="tabular-nums"
              >
                {d.promedio}%
              </Badge>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// ── Insights Section [VZ-30] ────────────────────────────────────

const INSIGHT_ICONS: Record<string, React.ElementType> = {
  sentiment: TrendingUp,
  topic: Lightbulb,
  ai: Sparkles,
  info: Lightbulb,
};

function InsightsSection({ insights }: { insights: InsightItem[] }) {
  if (insights.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Lightbulb className="size-4 text-yellow-500" />
          Insights automáticos
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {insights.map((ins, i) => {
            const Icon = INSIGHT_ICONS[ins.icono] ?? Lightbulb;
            return (
              <div key={i} className="flex items-start gap-3">
                <Icon className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
                <p className="text-sm">{ins.texto}</p>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

// ── Recent Activity ─────────────────────────────────────────────

const ESTADO_CONFIG: Record<
  string,
  { icon: React.ElementType; color: string; label: string }
> = {
  procesado: {
    icon: CheckCircle2,
    color: "text-green-500",
    label: "Procesado",
  },
  procesando: { icon: Loader2, color: "text-blue-500", label: "Procesando" },
  error: { icon: XCircle, color: "text-red-500", label: "Error" },
  subido: { icon: Upload, color: "text-muted-foreground", label: "Subido" },
};

function ActividadSection({ actividad }: { actividad: ActividadReciente[] }) {
  if (actividad.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Clock className="size-4 text-muted-foreground" />
            Actividad reciente
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            No hay actividad reciente.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Clock className="size-4 text-muted-foreground" />
          Actividad reciente
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {actividad.map((a, i) => {
            const cfg = ESTADO_CONFIG[a.estado] ?? ESTADO_CONFIG.subido;
            const StatusIcon = cfg.icon;
            const fecha = new Date(a.fecha);
            return (
              <div key={i} className="flex items-center gap-3">
                <StatusIcon className={`size-4 shrink-0 ${cfg.color}`} />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">
                    {a.documento_nombre}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {a.evaluaciones_extraidas} evaluaciones ·{" "}
                    {fecha.toLocaleDateString("es", {
                      day: "numeric",
                      month: "short",
                    })}
                  </p>
                </div>
                <Badge variant="outline" className="text-xs">
                  {cfg.label}
                </Badge>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

// ── Quick Actions ───────────────────────────────────────────────

const QUICK_ACTIONS = [
  { label: "Subir PDF", href: "/evaluacion-docente/carga", icon: Upload },
  {
    label: "Biblioteca",
    href: "/evaluacion-docente/biblioteca",
    icon: Library,
  },
  {
    label: "Estadísticas",
    href: "/evaluacion-docente/estadisticas",
    icon: BarChart3,
  },
  {
    label: "Consultas IA",
    href: "/evaluacion-docente/consultas-ia",
    icon: Sparkles,
  },
];

function QuickActions() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Acciones rápidas</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {QUICK_ACTIONS.map((action) => (
            <Link
              key={action.href}
              href={action.href}
              className="inline-flex h-auto flex-col items-center justify-center gap-1.5 rounded-lg border border-border bg-background px-2.5 py-3 text-sm font-medium transition-colors hover:bg-muted hover:text-foreground"
            >
              <action.icon className="size-5" />
              <span className="text-xs">{action.label}</span>
            </Link>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// ── Main Command Center ─────────────────────────────────────────

export function CommandCenter() {
  const {
    dashboard,
    alertSummary,
    criticalAlerts,
    isLoading,
    isEmpty,
    error,
    modalidad,
    setModalidad,
    refetch,
  } = useCommandCenter();

  if (isLoading && !dashboard) return <DashboardSkeleton />;
  if (error) return <DashboardError message={error} onRetry={refetch} />;

  if (isEmpty || !dashboard) {
    return (
      <div className="space-y-6">
        <ModalidadSelector value={modalidad} onChange={setModalidad} />
        <DashboardEmpty />
      </div>
    );
  }

  const {
    kpis,
    tendencia,
    top_docentes,
    bottom_docentes,
    insights,
    actividad_reciente,
  } = dashboard;

  return (
    <div className="space-y-6">
      {/* Modalidad Filter [BR-MOD-05] */}
      <ModalidadSelector value={modalidad} onChange={setModalidad} />

      {/* KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          label="Documentos procesados"
          value={kpis.documentos_procesados}
          icon={FileText}
          accent="text-blue-500"
        />
        <KpiCard
          label="Docentes evaluados"
          value={kpis.docentes_evaluados}
          icon={Users}
          accent="text-emerald-500"
        />
        <KpiCard
          label="Promedio general"
          value={`${kpis.promedio_general}%`}
          icon={TrendingUp}
          accent="text-violet-500"
        />
        <KpiCard
          label="Alertas activas"
          value={alertSummary?.total_activas ?? kpis.alertas_criticas}
          icon={AlertTriangle}
          accent={
            (alertSummary?.total_activas ?? kpis.alertas_criticas) > 0
              ? "text-red-500"
              : "text-emerald-500"
          }
          description={
            alertSummary
              ? `${alertSummary.docentes_afectados} docente${alertSummary.docentes_afectados !== 1 ? "s" : ""}`
              : undefined
          }
        />
      </div>

      {/* Alert Summary + Critical Alerts */}
      <div className="grid gap-6 lg:grid-cols-2">
        {alertSummary && <AlertSummaryBar summary={alertSummary} />}
        <CriticalAlertsPanel alerts={criticalAlerts} />
      </div>

      {/* Trend Chart */}
      <TendenciaChart data={tendencia} />

      {/* Top / Bottom Docentes */}
      <div className="grid gap-6 lg:grid-cols-2">
        <DocenteList
          title="Top docentes"
          icon={Trophy}
          docentes={top_docentes}
          variant="top"
        />
        <DocenteList
          title="Docentes con menor puntaje"
          icon={ArrowDown}
          docentes={bottom_docentes}
          variant="bottom"
        />
      </div>

      {/* Insights + Activity */}
      <div className="grid gap-6 lg:grid-cols-2">
        <InsightsSection insights={insights} />
        <ActividadSection actividad={actividad_reciente} />
      </div>

      {/* Quick Actions */}
      <QuickActions />
    </div>
  );
}
