"use client";

export function QuerySkeleton() {
  return (
    <div className="space-y-4">
      <div className="h-[120px] animate-pulse rounded-xl bg-muted/60" />
      <div className="h-[200px] animate-pulse rounded-xl bg-muted/60" />
    </div>
  );
}

export function QueryError({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <div className="flex min-h-[200px] flex-col items-center justify-center gap-4 rounded-xl border border-destructive/30 bg-destructive/5 p-8 text-center">
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
