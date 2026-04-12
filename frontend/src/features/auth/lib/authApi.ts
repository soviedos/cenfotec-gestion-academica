/** Auth API client helpers — calls to backend /auth endpoints. */

const AUTH_BASE = "/api/v1/auth";

export async function fetchCurrentUser() {
  const res = await fetch(`${AUTH_BASE}/me`, { credentials: "include" });
  if (!res.ok) return null;
  return res.json();
}

export async function logout() {
  await fetch(`${AUTH_BASE}/logout`, {
    method: "POST",
    credentials: "include",
  });
}
