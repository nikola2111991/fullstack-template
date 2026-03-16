/**
 * Next.js API Response Helpers — Consistent {data, error, meta} format
 * Usage: return success(users); return notFound(); return validationError("Email required", "email");
 */

import { NextResponse } from "next/server";

function meta() {
  return { timestamp: new Date().toISOString(), requestId: crypto.randomUUID() };
}

export function success<T>(data: T, status = 200) {
  return NextResponse.json({ data, error: null, meta: meta() }, { status });
}

export function created<T>(data: T) { return success(data, 201); }

export function error(code: string, message: string, status = 400, field?: string) {
  return NextResponse.json({ data: null, error: { code, message, field }, meta: meta() }, { status });
}

export function notFound(msg = "Resource not found") { return error("NOT_FOUND", msg, 404); }
export function unauthorized(msg = "Authentication required") { return error("UNAUTHORIZED", msg, 401); }
export function forbidden(msg = "Access denied") { return error("FORBIDDEN", msg, 403); }
export function validationError(msg: string, field?: string) { return error("VALIDATION_ERROR", msg, 422, field); }

export function rateLimited(retryAfter = 60) {
  const resp = error("RATE_LIMITED", "Too many requests", 429);
  resp.headers.set("Retry-After", String(retryAfter));
  return resp;
}

export function serverError(msg = "Internal server error") { return error("INTERNAL_ERROR", msg, 500); }
