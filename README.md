# Fullstack Template

Production-ready template for Next.js + FastAPI projects. Includes battle-tested patterns for API clients, error handling, database setup, caching, authentication, and more.

## Quick Start

1. Click **"Use this template"** on GitHub
2. Clone your new repo
3. Copy `templates/env.example` to `.env` and fill in your values
4. Start building

## What's Included

### CLAUDE.md

AI-powered development rules covering TypeScript strict mode, Python type hints, error recovery patterns, database conventions, caching strategies, monitoring, and deploy checklists. Drop this into any project to enforce consistent quality standards.

### Templates

| File | Purpose |
|------|---------|
| `api-client.ts` | TS fetch wrapper (retry, timeout, AbortSignal, typed errors) |
| `api-response.ts` | Next.js response helpers ({data, error, meta}) |
| `api_client.py` | Python async wrapper (httpx + tenacity) |
| `circuit_breaker.py` | Circuit breaker with logging and stats |
| `database.py` | Async SQLAlchemy + session + transactions |
| `fastapi_base.py` | FastAPI factory, config, error handlers, health |
| `fastapi_middleware.py` | FastAPI request ID + logging + rate limit + auth |
| `middleware.ts` | Next.js auth + rate limiting |
| `logging_config.py` | Structured JSON/text logging |
| `scraper.py` | Async scraper (rate limited, retry, CSV/JSON export) |
| `test_patterns.py` | pytest fixtures, mocks, AAA pattern |
| `use-fetch.ts` | React hooks: useFetch + useMutation |
| `error-boundary.tsx` | React Error Boundary with fallback UI |
| `seo.tsx` | Next.js metadata + JSON-LD helpers |
| `zod-schemas.ts` | Shared Zod schemas (user, pagination, API response) |
| `discord_bot.py` | Discord bot base with cogs pattern |
| `Dockerfile` | Multi-stage Python production build |
| `docker-compose.yml` | Full stack: frontend + backend + db + redis |
| `env.example` | Template for all env variables |

### CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`) with:
- Frontend: ESLint, TypeScript check, build
- Backend: ruff, mypy, pytest (80% coverage gate)
- Dependency caching for fast runs

## Tech Stack

**Frontend:** Next.js 14+ (App Router), TypeScript (strict), Tailwind CSS, Framer Motion
**Backend:** Python 3.11+ (typed), FastAPI, SQLAlchemy (async)
**Database:** Supabase (Postgres), Redis (cache)
**Deploy:** Vercel (frontend), Railway/Fly.io (backend)
**Testing:** pytest, Vitest, 80%+ coverage

## File Structure

```
Next.js:
src/app/
components/{ui,layout,sections}/
lib/{utils,types,api-client,schemas}.ts
hooks/
public/

FastAPI:
backend/app/{main,config,dependencies}.py
routers/
models/
services/
db/
utils/
tests/
```

## License

MIT
