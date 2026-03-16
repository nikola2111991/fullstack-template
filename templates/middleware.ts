/**
 * Next.js Middleware — Auth + Rate limiting
 * Place in src/middleware.ts
 */
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_PATHS = ["/", "/api/health", "/login", "/register"];
const PUBLIC_PREFIXES = ["/api/public/", "/_next/", "/favicon"];

interface RateLimitEntry { count: number; resetTime: number; }
const store = new Map<string, RateLimitEntry>();

function checkRateLimit(key: string, max = 100, windowMs = 60000) {
  const now = Date.now();
  const entry = store.get(key);
  if (!entry || now > entry.resetTime) {
    store.set(key, { count: 1, resetTime: now + windowMs });
    return { limited: false, remaining: max - 1 };
  }
  entry.count++;
  if (entry.count > max) return { limited: true, remaining: 0, retryAfter: Math.ceil((entry.resetTime - now) / 1000) };
  return { limited: false, remaining: max - entry.count };
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (pathname.startsWith("/api/")) {
    const ip = request.headers.get("x-forwarded-for") ?? "anon";
    const { limited, remaining, retryAfter } = checkRateLimit(ip);
    if (limited) return NextResponse.json({ data: null, error: { code: "RATE_LIMITED", message: "Too many requests" } }, { status: 429, headers: { "Retry-After": String(retryAfter) } });
    const response = NextResponse.next();
    response.headers.set("X-RateLimit-Remaining", String(remaining));
    return response;
  }

  const isPublic = PUBLIC_PATHS.includes(pathname) || PUBLIC_PREFIXES.some(p => pathname.startsWith(p));
  if (!isPublic) {
    const token = request.headers.get("authorization")?.slice(7) ?? request.cookies.get("session-token")?.value;
    if (!token) {
      if (pathname.startsWith("/api/")) return NextResponse.json({ data: null, error: { code: "UNAUTHORIZED", message: "Auth required" } }, { status: 401 });
      return NextResponse.redirect(new URL("/login", request.url));
    }
  }
  return NextResponse.next();
}

export const config = { matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"] };
