# KAVACH v2 — Testing, Stability & "Never Break" Protocol

Governing principle: **the app must be demoable at the end of every phase.** Not "will be demoable after the next phase" — demoable today, from a fresh clone.

---

## 1. The Stability Contract (applies from Phase 0, forever)

1. **`main` is always green and always demoable.** Work on short-lived branches; merge only when CI + smoke pass.
2. **The Smoke Suite (`make smoke`)** is a scripted end-to-end run against docker-compose: boot all services → login as each role → submit a case (mock LLM) → watch it reach `clustered` → Shield check resolves → graph endpoint returns the campaign → evidence export verifies. **≤3 minutes, zero manual steps.** Grows one assertion per new feature. Runs in CI on every merge and locally before every phase gate.
3. **No feature is "done" until its `FEATURE_STATUS.md` row says `implemented` with its test IDs listed** — and the smoke suite still passes.
4. **Migration safety:** every Alembic migration tested up AND down against a seeded DB in CI.
5. **Fresh-clone check at every phase gate:** delete containers + volumes → `git clone` → `cp .env.example .env` → `docker compose up` → `make seed-demo && make smoke`. If a phase gate passes only on the developer's machine, it did not pass.

## 2. Test Pyramid & Per-Phase Regression

| Layer | Tooling | Rule |
|---|---|---|
| Unit (services, algorithms, de-id, chain, extraction) | pytest | Accompany every service; deterministic, no network |
| API/integration | pytest + httpx + compose Postgres/Redis | Authz matrix, state machine, rate limits, pagination |
| Frontend | Vitest components + Playwright flows | Every view's empty/loading/error states asserted |
| E2E smoke | `make smoke` | See §1.2 |
| Eval | `make eval` (doc 05 §2) | Accuracy regression gate: F1 drop >3 pts fails CI |
| Load/chaos | Locust + kill scripts (Phase 5, then kept) | Re-run before submission |

**Phase-end regression protocol (execute verbatim, every phase):**
1. `make test` (all unit+integration) → 100% pass, coverage not lower than previous phase.
2. `make smoke` on fresh clone (§1.5).
3. `make eval` in replay mode → no accuracy regression (from Phase 2 onward).
4. Playwright suite → pass (from Phase 4 onward).
5. Re-run the previous phase's gate checklist — earlier gates must STILL pass (this is the "does not break" guarantee).
6. Record results in `FEATURE_STATUS.md` §Gate Log with date + git SHA. A red item blocks the next phase, no exceptions.

## 3. API-Key Conservation Policy (strict — real key is almost never used)

`LLM_MODE` env controls everything; the same switch governs embeddings (`EMBED_MODE` follows unless overridden).

| Mode | What happens | When |
|---|---|---|
| `mock` (DEFAULT) | `MockLLMClient` returns deterministic verdicts derived from input keywords (scam template → matching verdict). No network, no key needed. | All unit/integration/CI/smoke tests, all day-to-day dev |
| `replay` | Serves cached real responses from `data/llm_cache/` (keyed by input hash). Cache misses FAIL loudly — never silently call live. | Eval runs, realistic UI dev, benchmark CI |
| `live` | Real API. Requires key AND `LLM_LIVE_ACK=yes` env var (double opt-in). Hard budget: `LLM_DAILY_BUDGET` (default $2) → auto-degrades to rules-only when hit. Every call logged with cost. | ONLY: (a) one-time paraphrase/cache generation per phase, (b) final pre-demo rehearsals, (c) the demo itself |

Enforcement, not convention:
- `mock` is the default in `.env.example`, compose, CI, and test fixtures. Tests **assert** `LLM_MODE != "live"` in a session-scoped fixture and abort otherwise.
- CI has no key secret at all — live calls in CI are impossible.
- The cache is committed (responses are de-identified text only — safe), so a fresh clone gets full replay capability with zero API calls.
- Expected total live usage across the whole project: **a few hundred calls** (cache builds + rehearsals + demo), not thousands.

## 4. Chaos & Resilience Drills (Phase 5, scripted in `infra/chaos/`)
- `kill_llm.sh`: block provider egress → assert degraded badge + rules verdicts + zero 500s.
- `kill_worker.sh`: SIGKILL a worker mid-job → assert retry drains queue, no case stuck.
- `restart_pg.sh`: restart Postgres under load → API returns typed 503s, recovers <30s, chain verifies after.
- Each drill = an automated assertion script, run before submission, results in the demo doc.

## 5. Demo-Day Insurance
- `make seed-demo` restores the exact demo dataset + eval state, idempotent.
- Every demo beat has a fallback: pre-recorded segment of that beat (recorded during Phase 6 rehearsals) — no live single point of failure.
- Rehearsal rule: the full demo script runs 3× clean on the fresh-clone build before recording day.
