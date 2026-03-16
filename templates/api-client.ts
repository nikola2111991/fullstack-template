/**
 * TypeScript API Client: Retry, timeout, typed errors
 * Usage: const { data, error } = await typedFetch<User[]>("/api/users");
 */

interface ApiResponse<T> {
  data: T | null;
  error: { code: string; message: string; status: number } | null;
}

interface ApiCallOptions {
  retries?: number;
  timeoutMs?: number;
}

export async function apiCall<T>(
  fn: (signal: AbortSignal) => Promise<T>,
  options?: ApiCallOptions
): Promise<ApiResponse<T>> {
  const { retries = 3, timeoutMs = 10000 } = options ?? {};

  for (let attempt = 0; attempt <= retries; attempt++) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const result = await fn(controller.signal);
      clearTimeout(timeout);
      return { data: result, error: null };
    } catch (err) {
      clearTimeout(timeout);
      if (attempt === retries) {
        const isTimeout = err instanceof DOMException && err.name === "AbortError";
        return {
          data: null,
          error: {
            code: isTimeout ? "TIMEOUT" : "API_ERROR",
            message: err instanceof Error ? err.message : "Unknown error",
            status: isTimeout ? 408 : 500,
          },
        };
      }
      await new Promise((r) => setTimeout(r, 1000 * 2 ** attempt));
    }
  }
  return { data: null, error: { code: "UNREACHABLE", message: "Max retries", status: 500 } };
}

export async function typedFetch<T>(
  path: string,
  options?: RequestInit & { baseUrl?: string; retries?: number; timeoutMs?: number }
): Promise<ApiResponse<T>> {
  const { baseUrl = "", retries = 3, timeoutMs = 10000, ...fetchOptions } = options ?? {};
  return apiCall<T>(async (signal) => {
    const response = await fetch(`${baseUrl}${path}`, {
      ...fetchOptions,
      signal,
      headers: { "Content-Type": "application/json", ...fetchOptions.headers },
    });
    if (!response.ok) throw new Error(`${response.status}: ${await response.text()}`);
    return response.json();
  }, { retries, timeoutMs });
}
