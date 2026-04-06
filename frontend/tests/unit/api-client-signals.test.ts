import { describe, it, expect, vi, beforeEach } from "vitest";
import { apiClient, ApiClientError } from "@/lib/api-client";

describe("apiClient — AbortSignal support", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("GET passes signal to fetch", async () => {
    const controller = new AbortController();
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify({ ok: true }), { status: 200 }),
    );

    await apiClient.get("/test", controller.signal);

    const [, options] = vi.mocked(fetch).mock.calls[0];
    expect(options?.signal).toBe(controller.signal);
  });

  it("POST passes signal to fetch", async () => {
    const controller = new AbortController();
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify({ ok: true }), { status: 200 }),
    );

    await apiClient.post("/test", { q: "hello" }, controller.signal);

    const [, options] = vi.mocked(fetch).mock.calls[0];
    expect(options?.signal).toBe(controller.signal);
  });

  it("aborted signal causes fetch to reject with AbortError", async () => {
    const controller = new AbortController();
    controller.abort();

    vi.spyOn(globalThis, "fetch").mockRejectedValueOnce(
      new DOMException("The operation was aborted.", "AbortError"),
    );

    await expect(apiClient.get("/test", controller.signal)).rejects.toThrow(
      "The operation was aborted.",
    );
  });
});

describe("apiClient — error scenarios", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("500 response throws ApiClientError with status", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "Server error" }), {
        status: 500,
        statusText: "Internal Server Error",
      }),
    );

    try {
      await apiClient.get("/failing");
      expect.fail("should have thrown");
    } catch (e) {
      expect(e).toBeInstanceOf(ApiClientError);
      expect((e as ApiClientError).status).toBe(500);
      expect((e as ApiClientError).body).toEqual({ detail: "Server error" });
    }
  });

  it("429 response throws ApiClientError for rate limiting", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "Too many requests" }), {
        status: 429,
        statusText: "Too Many Requests",
      }),
    );

    try {
      await apiClient.post("/api/v1/query", { question: "test" });
      expect.fail("should have thrown");
    } catch (e) {
      expect(e).toBeInstanceOf(ApiClientError);
      expect((e as ApiClientError).status).toBe(429);
    }
  });

  it("network failure throws native Error", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValueOnce(
      new TypeError("Failed to fetch"),
    );

    await expect(apiClient.get("/unreachable")).rejects.toThrow(
      "Failed to fetch",
    );
  });

  it("non-JSON error body is handled gracefully", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response("plain text error", {
        status: 502,
        statusText: "Bad Gateway",
      }),
    );

    try {
      await apiClient.get("/bad-gateway");
      expect.fail("should have thrown");
    } catch (e) {
      expect(e).toBeInstanceOf(ApiClientError);
      expect((e as ApiClientError).body).toBeNull();
    }
  });
});
