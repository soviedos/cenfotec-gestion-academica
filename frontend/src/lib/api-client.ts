import { getToken } from "@/features/auth/lib/authApi";

const API_BASE_URL = "";

class ApiClientError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public body: unknown,
  ) {
    super(`API error: ${status} ${statusText}`);
    this.name = "ApiClientError";
  }
}

type RequestOptions = {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
  signal?: AbortSignal;
};

function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(
  endpoint: string,
  options: RequestOptions = {},
): Promise<T> {
  const { method = "GET", body, headers = {}, signal } = options;

  const config: RequestInit = {
    method,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...headers,
    },
    signal,
  };

  if (body) {
    config.body = JSON.stringify(body);
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    throw new ApiClientError(response.status, response.statusText, errorBody);
  }

  return response.json();
}

async function uploadFile<T>(
  endpoint: string,
  file: File,
  signal?: AbortSignal,
): Promise<T> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: "POST",
    body: formData,
    headers: authHeaders(),
    signal,
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    throw new ApiClientError(response.status, response.statusText, errorBody);
  }

  return response.json();
}

export const apiClient = {
  get: <T>(endpoint: string, signal?: AbortSignal) =>
    request<T>(endpoint, { signal }),
  post: <T>(endpoint: string, body: unknown, signal?: AbortSignal) =>
    request<T>(endpoint, { method: "POST", body, signal }),
  put: <T>(endpoint: string, body: unknown, signal?: AbortSignal) =>
    request<T>(endpoint, { method: "PUT", body, signal }),
  patch: <T>(endpoint: string, body: unknown, signal?: AbortSignal) =>
    request<T>(endpoint, { method: "PATCH", body, signal }),
  delete: <T>(endpoint: string, signal?: AbortSignal) =>
    request<T>(endpoint, { method: "DELETE", signal }),
  upload: <T>(endpoint: string, file: File, signal?: AbortSignal) =>
    uploadFile<T>(endpoint, file, signal),
};

export { ApiClientError };
