/**
 * Thin fetch wrapper for the Sudoke backend.
 *
 * The admin UI calls the API from the server side using a configured admin
 * principal. In dev this uses the X-Dev-Auth-User bypass; in production this
 * would be a real Clerk JWT exchanged via a server-side session.
 */

import 'server-only';

const API_BASE_URL = process.env.API_BASE_URL ?? 'http://localhost:8000/api/v1';
const ADMIN_PRINCIPAL = process.env.ADMIN_AUTH_PROVIDER_ID ?? 'admin-dev';
const ADMIN_BEARER = process.env.ADMIN_API_BEARER;

interface ApiOptions extends Omit<RequestInit, 'body'> {
  readonly body?: unknown;
}

export class ApiError extends Error {
  readonly status: number;
  readonly issues?: readonly string[];
  constructor(status: number, message: string, issues?: readonly string[]) {
    super(message);
    this.status = status;
    if (issues) {
      this.issues = issues;
    }
  }
}

export async function apiFetch<T>(path: string, opts: ApiOptions = {}): Promise<T> {
  const { body, headers, ...rest } = opts;
  const finalHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-Dev-Auth-User': ADMIN_PRINCIPAL,
    ...(ADMIN_BEARER ? { Authorization: `Bearer ${ADMIN_BEARER}` } : {}),
    ...(headers as Record<string, string> | undefined),
  };

  const init: RequestInit = {
    ...rest,
    headers: finalHeaders,
    cache: 'no-store',
  };
  if (body !== undefined) {
    init.body = JSON.stringify(body);
  }
  const res = await fetch(`${API_BASE_URL}${path}`, init);

  if (!res.ok) {
    let detail = res.statusText;
    let issues: string[] | undefined;
    try {
      const json = (await res.json()) as { detail?: string | { detail?: string; issues?: string[] }; issues?: string[] };
      if (typeof json.detail === 'string') detail = json.detail;
      else if (json.detail && typeof json.detail === 'object') {
        if (typeof json.detail.detail === 'string') detail = json.detail.detail;
        issues = json.detail.issues;
      }
      if (!issues && json.issues) issues = json.issues;
    } catch {
      // body wasn't JSON
    }
    throw new ApiError(res.status, detail, issues);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}
