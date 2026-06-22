# AGENTS.md — KAVACH

This file orients any AI coding agent (Claude Code, etc.) working in this repository. Read this before making changes. For deeper detail, follow the links rather than guessing.

## What this project is

KAVACH is a three-module fraud-intelligence platform: **FraudScope** (classifies a single piece of suspicious text via Claude API into a structured fraud verdict), **NetworkX** (clusters classified cases into fraud-ring graphs via shared infrastructure + script similarity), **CrimeMap** (aggregates cases geospatially into an enforcement-priority ranking). The product's core value is the *chain* — one case flowing through all three modules — not any module in isolation. Never build or change a module in a way that breaks that chain.

Related docs (read the relevant one before touching that area):
- `ARCHITECTURE.md` — system design, data flow, scalability roadmap
- `DATABASE_SCHEMA.md` — full schema, do not deviate from field names here without updating this file too
- `FEATURE_REQUIREMENTS.md` — functional specs per module, MVP vs later tiers
- `FRONTEND_PLAN.md` — design tokens, component map, UI conventions
- `GUIDELINES.md` — coding style, git workflow, security rules

## Tech stack (do not introduce alternatives without discussion)

- Backend: Python, FastAPI, SQLAlchemy, Pydantic v2, SQLite (dev) → Postgres (prod path)
- LLM: Anthropic API, model `claude-sonnet-4-6`, structured JSON output only
- Graph: `networkx` + `python-louvain` for community detection
- Frontend: React, Tailwind (core utility classes only, no Tailwind compiler plugins), D3 v7 for graph + choropleth
- Containerization: Docker, single `docker-compose.yml` for local dev (backend + frontend + db)

## Hard rules — never violate these

1. **Never send raw PII to the Claude API.** All phone numbers, Aadhaar-like 12-digit numbers, and bank account fragments must pass through the de-identification step (see `ARCHITECTURE.md` §Data Flow) before any LLM call. This is a legal/safety requirement, not a style preference.
2. **Never trust raw LLM output.** Every Claude response must be validated against the Pydantic schema in `app/schemas.py` before it touches the database or the frontend. On validation failure, retry once, then degrade to `needs_manual_review` — never silently pass through unvalidated text.
3. **Every classification must produce an `audit_id` and be persisted, including failures.** Auditability is a headline feature of this product — code that classifies without logging breaks the pitch, not just the code.
4. **Don't build UI that looks like a chat interface.** No chat bubbles, no centered single-column "assistant is typing" patterns. See `FRONTEND_PLAN.md` for the actual design direction — this is intentional and load-bearing for the product's positioning.
5. **Field names in code must match `DATABASE_SCHEMA.md` exactly.** If you need a new field, add it to that file in the same change, don't let schema drift happen silently.

## How to run locally

```
docker-compose up --build
# backend: http://localhost:8000  (docs at /docs)
# frontend: http://localhost:3000
```

Environment variables needed (see `.env.example`): `ANTHROPIC_API_KEY`, `DATABASE_URL`, `CORS_ORIGINS`.

## Before opening a PR / finishing a task

- Run backend tests: `pytest app/tests`
- Run frontend lint: `npm run lint`
- Confirm the end-to-end chain still works manually: submit a case in FraudScope → confirm it appears on the NetworkX graph → confirm its district shows up in CrimeMap's campaign count. This chain is the single most important regression check in the whole project.
- Update `FEATURE_REQUIREMENTS.md` checkboxes if you completed a tracked feature.

## When uncertain

If a requirement is ambiguous, default to the MVP definition in `FEATURE_REQUIREMENTS.md` rather than guessing at scope. Smaller and working beats larger and half-done — this mirrors the project's own build philosophy.
