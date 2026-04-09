import { describe, it, expect } from "vitest";
import { buildQuery } from "@/lib/api/query-builder";

describe("buildQuery", () => {
  it("builds query string from params", () => {
    const result = buildQuery({ page: 1, periodo: "C1 2025" });
    expect(result).toBe("?page=1&periodo=C1+2025");
  });

  it("filters out undefined values", () => {
    const result = buildQuery({ page: 1, docente: undefined });
    expect(result).toBe("?page=1");
  });

  it("filters out null values", () => {
    const result = buildQuery({
      page: 1,
      docente: null as unknown as undefined,
    });
    expect(result).toBe("?page=1");
  });

  it("filters out empty strings", () => {
    const result = buildQuery({ page: 1, docente: "" });
    expect(result).toBe("?page=1");
  });

  it("returns empty string when all values are empty", () => {
    const result = buildQuery({
      a: undefined,
      b: "",
      c: undefined,
    });
    expect(result).toBe("");
  });

  it("returns empty string for empty params", () => {
    expect(buildQuery({})).toBe("");
  });

  it("converts numbers to strings", () => {
    const result = buildQuery({ limit: 50, offset: 0 });
    expect(result).toContain("limit=50");
    expect(result).toContain("offset=0");
  });

  it("keeps zero as a valid value", () => {
    const result = buildQuery({ offset: 0 });
    expect(result).toBe("?offset=0");
  });
});
