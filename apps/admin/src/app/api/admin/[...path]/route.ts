import { NextResponse, type NextRequest } from 'next/server';
import { apiFetch, ApiError } from '@/lib/api';

/**
 * Server-side proxy that forwards admin actions from client components
 * (which can't safely hold the API bearer/dev token) to the FastAPI backend.
 */

async function forward(
  req: NextRequest,
  context: { params: Promise<{ path: string[] }> },
  method: 'GET' | 'POST' | 'PATCH' | 'DELETE',
): Promise<NextResponse> {
  const { path } = await context.params;
  const search = req.nextUrl.search;
  const target = `/admin/${path.join('/')}${search}`;
  const body = method === 'GET' || method === 'DELETE' ? undefined : await req.json().catch(() => undefined);
  try {
    const data = await apiFetch<unknown>(target, { method, body });
    return NextResponse.json(data ?? {});
  } catch (err) {
    if (err instanceof ApiError) {
      const payload: Record<string, unknown> = { detail: err.message };
      if (err.issues) payload.issues = err.issues;
      return NextResponse.json(payload, { status: err.status });
    }
    return NextResponse.json(
      { detail: err instanceof Error ? err.message : 'Unknown error' },
      { status: 500 },
    );
  }
}

export const GET = (req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) =>
  forward(req, ctx, 'GET');
export const POST = (req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) =>
  forward(req, ctx, 'POST');
export const PATCH = (req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) =>
  forward(req, ctx, 'PATCH');
export const DELETE = (req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) =>
  forward(req, ctx, 'DELETE');
