# CLAUDE.md — Agent Instructions for Building KAVACH v2

> Copy this file to the root of the build repo. It governs every Claude session working on this codebase.

## What this project is
KAVACH v2: fraud-defense platform (citizen Shield + law-enforcement intelligence Terminal) for ET AI Hackathon 2026 Problem #6. Canonical references, in priority order:
1. `ROADMAP.md` — current phase and gates. **Never work ahead of the current phase without being asked.**
2. `docs/01_PRODUCT_SPEC.md` — what to build. `docs/02_ARCHITECTURE.md` — how. `docs/03_SECURITY.md` — non-negotiable guardrails.
3. `legacy/` — v1 code, read-only reference. Reuse ideas, not files wholesale.

## Collaboration mode — work WITH the developer, not for them
- **Propose before building.** For any task > ~30 lines: state your plan in 3–6 bullets (files touched, approach, tradeoffs), wait for a go-ahead. Small fixes: just do them.
- **One decision at a time.** When a genuine fork exists (library, schema shape, API contract), present max 2–3 options with a recommendation. Don't silently pick on anything that's hard to reverse.
- **Explain as you go, briefly.** After each work chunk: what changed, why, what to review, what you're unsure about. The developer must be able to defend every line to judges.
- **Flag, don't bury.** If you notice a spec conflict, security smell, or a better approach — say so immediately, even mid-task.
- **Teach on request.** If the developer asks "why", give the reasoning + a pointer to the doc section, not just the answer.

## Session protocol (mandatory, every session)
- **Start:** read `FEATURE_STATUS.md` first. It is the ONLY authority on implemented vs pending. Never assume a feature exists because a doc describes it; never re-implement what's already `implemented`.
- **End:** update `FEATURE_STATUS.md` rows you touched (status + test IDs + notes). A session that changes code but not this file is incomplete.
- **Phase end:** execute the regression protocol in `docs/06_TESTING_AND_STABILITY.md §2` verbatim, log results in the Gate Log. Previous gates must still pass — the app is demoable at the end of EVERY phase, not just the last one.

## Hard rules (violating these fails the phase gate)
1. **No plaintext PII** outside `pii_vault` ciphertext. LLMs receive masked text only. Graph stores hashes only.
2. **No sync heavy work in request handlers.** LLM calls, embeddings, clustering → workers. Enforced by tests.
3. **Validate all LLM output server-side** (schema, enums, evidence-substring-exists). Never render it unescaped.
4. **Every endpoint has authz + a test in the authz matrix.** New endpoint without matrix row = incomplete.
5. **Migrations only** (Alembic). Never `create_all` in app code.
6. **No new dependency without one-line justification** in the PR/commit message. Pin everything.
7. **Tests accompany code** — worker jobs, services, and security behaviors especially. CI must stay green.
8. **Commit style:** conventional commits, small and thematic. Never commit venvs, node_modules, .env, DBs, model files.
9. **API key conservation:** `LLM_MODE=mock` is the default everywhere. Tests/CI/dev use `mock` or `replay` ONLY (`docs/06 §3`). `live` requires the developer's explicit say-so in that session, plus `LLM_LIVE_ACK=yes` and the budget guard. If you're about to make a live LLM call for anything other than cache-building, rehearsal, or the demo — stop and ask.
10. **MudraCheck is dropped.** Anything in `FEATURE_STATUS.md` §Parked is not to be built without explicit owner approval.

## Definition of Done (per task)
Code + tests + doc touch (update the relevant `docs/` file if behavior changed) + `FEATURE_STATUS.md` row updated + `make smoke` still green + runs in docker-compose. Ambiguity rule: if a spec detail is missing from `docs/04_FEATURE_DETAILS.md`, do NOT improvise silently — propose the interpretation, get a yes, then add it to the doc so the spec stays complete.

## Phase gates
At each phase end, run the gate checklist in `ROADMAP.md` verbatim and report results honestly. A red gate item blocks the next phase — say so rather than papering over it.

## Style
Backend: Python 3.12, FastAPI, type hints everywhere, ruff+mypy clean, services thin routes fat-services pattern. Frontend: TypeScript strict, functional components, design tokens from `agent/DESIGN_REFERENCE.md` — no ad-hoc colors/spacing. Errors: typed envelope `{success, data, error, trace_id}`; no bare `except`.

## When unsure
Ask one crisp question with your best-guess default attached ("I'll assume X unless you say otherwise"). Never stall, never invent requirements.
