/**
 * Shared query-string builder for API modules.
 *
 * Filters out undefined, null, and empty-string values so callers
 * can pass optional params without manual checks.
 */
export function buildQuery(
  params: Record<string, string | number | null | undefined> | object,
): string {
  const sp = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      sp.set(key, String(value));
    }
  }
  const q = sp.toString();
  return q ? `?${q}` : "";
}
