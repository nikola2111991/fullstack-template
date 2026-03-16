# FULL STACK DEV

## TECH STACK

**Frontend:** Next.js 14+ (App Router) · TypeScript (strict) · Tailwind CSS · Framer Motion
**Backend:** Python 3.11+ (typed) · FastAPI (preferred) · Flask · Django
**Data:** pandas · polars · numpy · BeautifulSoup · Scrapy · Playwright
**Testing:** pytest · Vitest · coverage 80%+
**Linting:** ruff (Python) · ESLint + Prettier (TS)
**Deploy:** Vercel (frontend) · Railway/Fly.io (backend)
**DB:** Supabase (Postgres) · Redis (cache)
**APIs:** Stripe/Paddle (payments) · Resend/ConvertKit (email) · Claude API/OpenAI (AI) · Google Places (maps) · HubSpot (CRM) · Clerk/NextAuth (auth) · Cal.com (scheduling) · PostHog (analytics)

## RULES

- TypeScript strict: never `any`, never `@ts-ignore`
- Python typed: type hints on everything, Pydantic for validation
- Mobile-first, responsive 320-1920px
- Performance: LCP < 2.5s, CLS < 0.1, FID < 100ms
- SEO by default: meta, OG tags, JSON-LD, unique H1, alt text
- API responses: consistent `{data, error, meta}` format
- Env vars for config, never hardcoded secrets
- Input validation on everything (Zod frontend, Pydantic backend)
- CORS whitelisted in production, never wildcard
- Component < 150 LOC, Python function < 50 LOC
- Error handling everywhere, never silently ignore
- Ship at 70%, iterate
- Never `datetime.utcnow()`, always `datetime.now(timezone.utc)`

## QUALITY CHECK

Before every output, verify:
1. **Types**: strict TS / Py type hints, no `any`
2. **Security**: env vars, input validation, no XSS, CORS config
3. **Performance**: bundle size, image opt, code splitting, async I/O
4. **Responsive**: mobile/tablet/desktop, hover/focus/active states
5. **SEO**: meta tags, OG, structured data (if frontend)
6. **Errors**: loading/error/empty states, try-catch, meaningful messages
7. **API**: validation, rate limiting, consistent responses, pagination

## ERROR RECOVERY

- **Critical (payment, auth):** Circuit Breaker + Retry 3x exponential + user-facing error
- **Non-critical:** Retry 3x + graceful degradation (cached/fallback)
- **Background job:** Retry 5x + log + alert
- **Webhook:** Verify signature + return 200 immediately + process async + idempotency key
- Never: retry without backoff, blocking > 10s, silent ignore

## DATABASE

- Async SQLAlchemy with connection pooling (pool_size=10, max_overflow=20)
- FastAPI dependency `get_db()` for session management
- `@transactional` decorator for atomic operations
- Migrations: Alembic with `alembic revision --autogenerate`
- Soft delete pattern: `deleted_at` timestamp instead of physical deletion
- Indexes on all foreign keys and frequently used WHERE columns
- UUID for primary keys in public APIs

## CACHING

- Redis cache-aside pattern: check cache, if miss read DB, write to cache
- TTL by type: user session 24h, API response 5min, static config 1h
- Cache invalidation: delete on write, don't wait for expiry
- Cache key format: `{entity}:{id}:{version}` (e.g. `user:123:v2`)
- Never cache: payment data, auth tokens, user PII without encryption

## MONITORING

- Structured JSON logging in production (timestamp, level, request_id, message)
- Health check endpoint: `/health` returns `{status, version, db_status}`
- Key metrics: response time p95 < 200ms, error rate < 1%, uptime > 99.9%
- Error tracking: Sentry for exceptions, PostHog for user analytics
- Log levels: ERROR (bugged), WARNING (degraded), INFO (business events), DEBUG (dev only)

## DEPLOY CHECKLIST

Before every deploy:
1. Env vars set (compare with `env.example`)
2. DB migrations run
3. Build passes without errors
4. Tests pass (coverage 80%+)
5. Lint clean (ruff, eslint)
6. CORS origins updated for production
7. Smoke test: health check, login flow, critical path

## TEMPLATES

`templates/` contains production-ready patterns. Use as a base, don't write from scratch:

| File | Purpose |
|------|---------|
| `api-client.ts` | TS fetch wrapper (retry, timeout, AbortSignal, typed errors) |
| `api-response.ts` | Next.js response helpers ({data, error, meta}) |
| `api_client.py` | Python async wrapper (httpx + tenacity) |
| `circuit_breaker.py` | Circuit breaker with logging and stats |
| `fastapi_base.py` | FastAPI factory, config, error handlers, health |
| `middleware.ts` | Next.js auth + rate limiting |
| `fastapi_middleware.py` | FastAPI request ID + logging + rate limit + auth |
| `test_patterns.py` | pytest fixtures, mocks, AAA pattern |
| `scraper.py` | Async scraper (rate limited, retry, CSV/JSON export) |
| `zod-schemas.ts` | Shared Zod schemas (user, pagination, API response) |
| `database.py` | Async SQLAlchemy + session + transactions |
| `use-fetch.ts` | React hooks: useFetch + useMutation |
| `error-boundary.tsx` | React Error Boundary with fallback UI |
| `seo.tsx` | Next.js metadata + JSON-LD helpers |
| `logging_config.py` | Structured JSON/text logging |
| `env.example` | Template for all env variables |
| `Dockerfile` | Multi-stage Python production build |
| `docker-compose.yml` | Full stack: frontend + backend + db + redis |
| `.dockerignore` | Docker context filter |

## FILE STRUCTURE

**Next.js:** `src/app/` · `components/{ui,layout,sections}/` · `lib/{utils,types,api-client,schemas}.ts` · `hooks/` · `public/`
**FastAPI:** `backend/app/{main,config,dependencies}.py` · `routers/` · `models/` · `services/` · `db/` · `utils/` · `tests/`

## DESIGN

- Typography = 80% of design, distinctive display font + clean body font
- Dominant + accent color, not 5 equal ones
- Whitespace is a feature, not empty space
- Animations = UX feedback, not decoration
- Dark mode ready (CSS variables)
- Forbidden: Inter/Roboto/Arial as primary, purple gradient hero, stock imagery, unstyled component libraries

## PYTHON

Thin routers, fat services · Pydantic Settings for config · Fail loud (never silent) · Async for I/O · `ruff` for linting

## GIT

`main` (prod) · `dev` · `feature/[description]` · Conventional commits · Never commit: node_modules, .env, __pycache__, .venv, .next
