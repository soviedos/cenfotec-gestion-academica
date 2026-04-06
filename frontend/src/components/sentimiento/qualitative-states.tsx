"use client";

export function QualitativeSkeleton() {
  return (
    <div className="space-y-6">
      {/* KPI row */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-27 animate-pulse rounded-xl bg-muted/60" />
        ))}
      </div>
      {/* Filter bar */}
      <div className="h-25 animate-pulse rounded-xl bg-muted/60" />
      {/* Charts row */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="h-95 animate-pulse rounded-xl bg-muted/60" />
        <div className="h-95 animate-pulse rounded-xl bg-muted/60" />
      </div>
      {/* Table */}
      <div className="h-75 animate-pulse rounded-xl bg-muted/60" />
    </div>
  );
}

export function QualitativeEmpty() {
  return (
    <div className="flex min-h-100 flex-col items-center justify-center gap-4 rounded-xl border border-dashed p-8 text-center">
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
            d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z"
          />
        </svg>
      </div>
      <div>
        <h3 className="text-lg font-semibold">Sin comentarios analizados</h3>
        <p className="mt-1 max-w-sm text-sm text-muted-foreground">
          Suba y procese evaluaciones docentes desde la sección de Carga para
          ver el análisis de sentimiento aquí.
        </p>
      </div>
    </div>
  );
}

export function QualitativeError({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <div className="flex min-h-100 flex-col items-center justify-center gap-4 rounded-xl border border-destructive/30 bg-destructive/5 p-8 text-center">
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
