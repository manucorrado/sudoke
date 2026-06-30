const LOCAL_API_BASE_URL = 'http://localhost:8000/api/v1';

interface ExpoProcessEnv {
  readonly EXPO_PUBLIC_API_BASE_URL?: string;
}

interface GlobalWithProcess {
  readonly process?: { readonly env?: ExpoProcessEnv };
}

const env = (globalThis as GlobalWithProcess).process?.env ?? {};

function normalizeBaseUrl(value: string | undefined): string {
  const baseUrl = value?.trim() || LOCAL_API_BASE_URL;
  return baseUrl.replace(/\/$/, '');
}

const BASE_URL = normalizeBaseUrl(env.EXPO_PUBLIC_API_BASE_URL);
const BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
}

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { body, headers, ...rest } = options;
  const requestBody = body !== undefined ? JSON.stringify(body) : undefined;

  const res = await fetch(`${BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
    ...(requestBody !== undefined ? { body: requestBody } : {}),
    ...rest,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new ApiError(res.status, text);
  }

  if (res.status === 204) return undefined as T;

  return res.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "GET" }),

  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "POST", body }),

  put: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "PUT", body }),

  patch: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "PATCH", body }),

  delete: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "DELETE" }),
};
