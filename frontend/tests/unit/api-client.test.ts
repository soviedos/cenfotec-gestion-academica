import { describe, it, expect, vi, beforeEach } from "vitest";
import { apiClient, ApiClientError } from "@/lib/api-client";

describe("apiClient", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("GET request returns parsed JSON", async () => {
    const mockData = { id: 1, name: "test" };
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify(mockData), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    const result = await apiClient.get<typeof mockData>("/test");
    expect(result).toEqual(mockData);
    expect(fetch).toHaveBeenCalledWith(
      "/test",
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("POST sends JSON body", async () => {
    const payload = { nombre: "Docente 1" };
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify({ id: "abc" }), { status: 201 }),
    );

    await apiClient.post("/docentes", payload);

    const [, options] = vi.mocked(fetch).mock.calls[0];
    expect(options?.method).toBe("POST");
    expect(options?.body).toBe(JSON.stringify(payload));
  });

  it("throws ApiClientError on non-ok response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "Not found" }), {
        status: 404,
        statusText: "Not Found",
      }),
    );

    await expect(apiClient.get("/missing")).rejects.toThrow(ApiClientError);

    try {
      vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "Error" }), {
          status: 500,
          statusText: "Internal Server Error",
        }),
      );
      await apiClient.get("/error");
    } catch (error) {
      expect(error).toBeInstanceOf(ApiClientError);
      expect((error as ApiClientError).status).toBe(500);
    }
  });
});

describe("ApiClientError", () => {
  it("includes status info in message", () => {
    const error = new ApiClientError(422, "Unprocessable Entity", {
      detail: "validation",
    });
    expect(error.message).toContain("422");
    expect(error.name).toBe("ApiClientError");
    expect(error.body).toEqual({ detail: "validation" });
  });
});
