# GUIDELINES.md — KAVACH Coding & Contribution Standards

## Python (backend)

- Python 3.11+, type hints on every function signature, no bare `dict`/`list` returns from endpoints — always a Pydantic model.
- Pydantic v2 for all request/response schemas. Schema definitions live in `app/schemas.py`, never inline in route handlers.
- Use `async def` for all route handlers that call the Claude API or hit the DB — don't block the event loop.
- One route file per module: `app/routes/fraudscope.py`, `app/routes/networkx.py`, `app/routes/crimemap.py`. Don't dump everything into `main.py`.
- Logging: use the standard `logging` module, never `print()`. Every Claude API call gets a log line with `audit_id`, latency, and success/failure — this log is part of the auditability story, treat it as a feature, not debug noise.
- Errors: return structured error responses `{ "error": str, "detail": str }` with appropriate HTTP status codes. Never let an unhandled exception leak a stack trace to the client.

## JavaScript / React (frontend)

- Functional components + hooks only. No class components.
- Tailwind core utility classes only (this environment doesn't support the Tailwind compiler/plugins — see `FRONTEND_PLAN.md` for the design token mapping).
- One component per file, colocate small subcomponents only if they're never reused elsewhere.
- State management: React context for cross-module case state (the "persistent context" requirement in `FEATURE_REQUIREMENTS.md`), local `useState` for everything else. Don't reach for Redux/Zustand unless the app genuinely outgrows context — it won't, in this scope.
- API calls go through a single `api/client.js` wrapper, never raw `fetch()` scattered through components — this is what makes swapping the backend URL or adding auth headers later a one-line change.

## API design conventions

- REST, plural nouns: `/cases`, `/cases/{id}`, `/districts/{name}/summary`.
- All timestamps in ISO 8601 UTC.
- All money values stored and transmitted as integers in paise (smallest unit), formatted to ₹ only at the display layer — never store floats for currency.

## Git workflow

- Branch naming: `module/short-description` (e.g. `fraudscope/pii-masking`, `frontend/graph-animation`).
- Commit messages: imperative mood, one line summary under 72 chars, body explains *why* not *what* if non-obvious (`git diff` already shows what).
- Don't commit `.env` files, mock data dumps over 1MB, or `node_modules`/`__pycache__` — confirm `.gitignore` covers these before first commit.

## Security & data handling

- No real PII in seed/mock data, ever — including in demo scripts. Use clearly fake patterns (e.g. `+91-XXXXX-00001`) for anything that touches a public repo.
- `ANTHROPIC_API_KEY` and any DB credentials live only in `.env`, never hardcoded, never logged.
- The de-identification step (masking phone/Aadhaar-like numbers before they reach the LLM) is mandatory and must run before *every* Claude API call, with no code path that skips it — see the hard rule in `AGENTS.md`.

## Testing expectations

- Backend: at minimum, a test that posts a known scam script and asserts the response validates against the Pydantic schema, and a test that posts garbage and confirms graceful `needs_manual_review` degradation rather than a crash.
- Frontend: not required to be exhaustive given the time box, but the three-module chain (case → graph → map) should have at least one manual test pass documented before any demo or submission.

## Documentation expectations

- Every new endpoint gets a one-line docstring describing what it does and what it expects, visible in FastAPI's auto-generated `/docs`.
- If you add a field to any database table, update `DATABASE_SCHEMA.md` in the same commit — schema and docs must never drift apart.

## Using AI coding assistants on this project

- Treat assistant-generated code as a first draft, not a final answer — review for the hard rules in `AGENTS.md` (PII handling, schema validation, audit logging) before merging, since these are easy for a model to silently omit if not explicitly prompted.
- Prefer giving the assistant one scoped task at a time (see the prompts in the build-plan doc) over one large "build the whole module" prompt — smaller scoped tasks are easier to verify correct.
