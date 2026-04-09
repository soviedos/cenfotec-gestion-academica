"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Generic hook for fetching data with abort-controller management,
 * loading state, and error handling.
 *
 * Best suited for hooks that fetch a single resource. For multi-fetch
 * hooks (e.g. useAnalytics), use the lower-level abort/error pattern
 * directly or compose multiple useApiFetch calls.
 *
 * @example
 * ```ts
 * function useDashboard() {
 *   return useApiFetch(
 *     (signal) => fetchDashboardSummary(signal),
 *     [],
 *     "Error al cargar el dashboard",
 *   );
 * }
 * ```
 */
export function useApiFetch<T>(
  fetcher: (signal: AbortSignal) => Promise<T>,
  deps: unknown[],
  errorMessage = "Error al cargar datos",
) {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const refetch = useCallback(async () => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setIsLoading(true);
    setError(null);

    try {
      const result = await fetcherRef.current(controller.signal);
      if (!controller.signal.aborted) {
        setData(result);
        setIsLoading(false);
      }
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      if (!controller.signal.aborted) {
        setError(err instanceof Error ? err.message : errorMessage);
        setIsLoading(false);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    refetch();
    return () => abortRef.current?.abort();
  }, [refetch]);

  return { data, isLoading, error, refetch };
}
