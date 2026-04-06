"use client";

import { Loader2 } from "lucide-react";

export function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      {/* KPI row */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-28 animate-pulse rounded-xl bg-muted/60" />
        ))}
      </div>
      {/* Charts row */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="h-[420px] animate-pulse rounded-xl bg-muted/60" />
        <div className="h-[420px] animate-pulse rounded-xl bg-muted/60" />
      </div>
      {/* Bottom row */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="h-[360px] animate-pulse rounded-xl bg-muted/60" />
        <div className="h-[360px] animate-pulse rounded-xl bg-muted/60" />
      </div>
    </div>
  );
}

export function DashboardLoading() {
  return (
    <div className="flex min-h-[400px] flex-col items-center justify-center gap-3">
      <Loader2 className="size-8 animate-spin text-muted-foreground" />
      <p className="text-sm text-muted-foreground">Cargando dashboard…</p>
    </div>
  );
}

export function DashboardEmpty() {
  return (
    <div className="flex min-h-[400px] flex-col items-center justify-center gap-4 rounded-xl border border-dashed p-8 text-center">
      <div className="rounded-full bg-muted p-4">
        <svg
          className="size-8 text-muted-foreground"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1.5}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z"
          />
        </svg>
      </div>
      <div>
        <h3 className="text-lg font-semibold">Sin datos de evaluaciones</h3>
        <p className="mt-1 max-w-sm text-sm text-muted-foreground">
          Suba archivos PDF de evaluaciones docentes desde la sección de Carga
          para ver el análisis estadístico aquí.
        </p>
      </div>
    </div>
  );
}

export function DashboardError({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <div className="flex min-h-[400px] flex-col items-center justify-center gap-4 rounded-xl border border-destructive/30 bg-destructive/5 p-8 text-center">
      <p className="text-sm text-destructive">{message}</p>
      <button
        onClick={onRetry}
        className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
      >
        Reintentar
      </button>
    </div>
  );
}
