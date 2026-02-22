import { getTokens, setTokens, clearTokens, isTokenExpired } from "./auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type RequestOptions = {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
};

let refreshPromise: Promise<boolean> | null = null;

async function refreshTokens(): Promise<boolean> {
  const { refreshToken } = getTokens();
  if (!refreshToken) return false;

  try {
    const res = await fetch(`${API_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    setTokens(data);
    return true;
  } catch {
    return false;
  }
}

async function ensureValidToken(): Promise<string | null> {
  const { accessToken } = getTokens();
  if (!accessToken) return null;

  if (!isTokenExpired(accessToken)) return accessToken;

  // Mutex: share a single refresh promise across concurrent requests
  if (!refreshPromise) {
    refreshPromise = refreshTokens().finally(() => {
      refreshPromise = null;
    });
  }

  const success = await refreshPromise;
  if (!success) {
    clearTokens();
    return null;
  }
  return getTokens().accessToken;
}

export async function apiClient<T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const token = await ensureValidToken();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...options.headers,
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, {
    method: options.method || "GET",
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  // If 401, try one refresh + retry
  if (res.status === 401 && token) {
    const refreshed = await refreshTokens();
    if (refreshed) {
      const newToken = getTokens().accessToken;
      const retryRes = await fetch(`${API_URL}${path}`, {
        method: options.method || "GET",
        headers: { ...headers, Authorization: `Bearer ${newToken}` },
        body: options.body ? JSON.stringify(options.body) : undefined,
      });

      if (retryRes.status === 204) return undefined as T;
      if (!retryRes.ok) {
        const err = await retryRes.json().catch(() => ({ detail: "Request failed" }));
        throw new Error(err.detail || `Request failed: ${retryRes.status}`);
      }
      return retryRes.json();
    } else {
      clearTokens();
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
      throw new Error("Session expired");
    }
  }

  if (res.status === 204) return undefined as T;

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }

  return res.json();
}
