import { describe, it, expect, vi, beforeEach } from "vitest";
import { getToken, setToken, clearToken } from "@/features/auth/lib/authApi";

// Use a simple in-memory storage mock since jsdom's localStorage is available
describe("Token storage", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("returns null when no token is stored", () => {
    expect(getToken()).toBeNull();
  });

  it("stores and retrieves a token", () => {
    setToken("my-jwt-token");
    expect(getToken()).toBe("my-jwt-token");
  });

  it("clears the stored token", () => {
    setToken("my-jwt-token");
    clearToken();
    expect(getToken()).toBeNull();
  });
});
