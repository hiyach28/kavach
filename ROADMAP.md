# KAVACH v2 — Build Roadmap

**Goal:** rebuild the hackathon prototype into a production-grade, unique product for ET AI Hackathon 2026 Problem #6 (Digital Public Safety), then produce the demo video and submission document.

**Strategy in one sentence:** keep v1's intelligence concepts (mask → classify → graph → takedown), rebuild the platform underneath them, and add the point-of-contact Shield layer that makes KAVACH unlike every post-complaint tool in the room.

**Reading order:** `docs/00_ASSESSMENT.md` (what exists) → `docs/01_PRODUCT_SPEC.md` (what we're building) → `docs/02_ARCHITECTURE.md` (how) → `docs/03_SECURITY.md` (guardrails) → `docs/04_FEATURE_DETAILS.md` (per-feature specs) → `docs/05_DATA_AND_METRICS.md` (datasets + stats) → `docs/06_TESTING_AND_STABILITY.md` (never-break protocol) → `docs/07_DEMO_PLAYBOOK.md` (video) → `agent/` (how developer + Claude work together).

**Two standing rules that apply to every phase:**
1. **Never-break:** at each phase end, run the regression protocol in `docs/06 §2` verbatim — all previous gates must still pass, `make smoke` must pass on a fresh clone, results logged in `FEATURE_STATUS.md` §Gate Log.
2. **Status truth:** `FEATURE_STATUS.md` is the single source of truth for implemented vs pending. Update it every session; never claim a feature that isn't `implemented` there.

**Estimates** assume one developer pairing with Claude (agent-assisted), part-time-to-full-time. Phases are sequential because each unblocks the next; tasks inside a phase can interleave.

---

## Phase 0 — Reset & Foundations (1–2 days)
*Nothing new gets built on a broken base.*

- Fresh repo structure per `docs/02_ARCHITECTURE.md §6`; new git history. Remove `.venv` (112MB), merge duplicate `Docs/`+`docs/`, real `.env.example`.
- Port the keepers from v1 as reference material into `legacy/` (read-only): LLM schemas/prompts, deidentify.py, clustering.py, D3 ForceGraph, CSS tokens.
- Tooling: `uv`/pip-tools pinned deps, ruff + mypy, pytest, ESLint + TypeScript for frontend, pre-commit hooks.
- CI: GitHub Actions — lint, typecheck, test, `bandit`, `pip-audit`, secret scan on every push.
- docker-compose with **all** services: api, worker, postgres(+pgvector), redis, frontend.

**Gate G0:** `docker compose up` → health checks green; CI green on main.

## Phase 1 — Secure Data & Auth Core (3–4 days)
*The disqualifying gaps first: auth, encryption, migrations.*

- Postgres schema + Alembic migrations (`docs/02 §4`), pgvector enabled.
- JWT auth + RBAC (4 roles) + district scoping; authz test matrix (every endpoint × role) written *first*.
- PII vault with AES-GCM envelope encryption; expanded de-identification (v1 regexes + email/PAN/URL/handle + NER names); decrypt endpoint with justification + audit.
- Hash-chained `audit_chain` with append-only DB grants; `verify.py`.
- Rate limiting, input caps, security headers, strict CORS, error envelope, pagination utilities.

**Gate G1:** authz matrix 100% pass; a DB dump contains zero plaintext PII; chain verification passes after 1k events.

## Phase 2 — Async Intelligence Pipeline (4–5 days)
*Fix the #1 scalability flaw; make classification production-grade.*

- Redis + arq (or Celery) workers; `POST /v1/cases` becomes enqueue-only (<200ms); SSE progress events.
- Provider-agnostic LLM client: Gemini primary, second provider fallback, rules-only degraded mode; server-side output validation (evidence substrings, enums); cost metering.
- Dedicated entity extraction (phones, UPI, accounts, URLs, handles, IFSC) → hashed `entities` graph tables.
- Embeddings → pgvector HNSW; ANN top-k replaces all-pairs cosine.
- **Incremental clustering** (affected-subgraph Louvain, per `docs/02 §D4`); nightly full recluster job; takedown-brief computation per campaign, cached.
- Batch CSV import (NCRP/1930-style) to bulk-seed realistic data.
- Data foundation (`docs/05 §1`): fetch real datasets (Kaggle fraud-call/scam-conversation sets, NCRB tables), synthetic seed generator with ground-truth manifest, benchmark-v1 + `make eval` harness.
- LLM mock/replay/live modes wired from the start (`docs/06 §3`) — CI and tests never touch the real API key.

**Gate G2:** 5,000 seeded cases; classify enqueue p95 <200ms; end-to-end case→campaign <30s; graph query p95 <500ms; clustering results match v1 quality on a fixture set.

## Phase 3 — Shield: Point-of-Contact Protection (5–6 days)
*The flagship differentiator. Build the demo centerpiece here.*

- `POST /v1/shield/check`: entity lookup → cached script-pattern ANN → LLM fallback; verdict bands + plain-language explanation; p95 <3s; per-IP rate limits.
- Language layer: detect + respond in kind (hi, en, ta, te, bn); localized verdict templates.
- Citizen PWA: dead-simple single screen — paste/share a message, number, UPI ID, or screenshot → verdict card; installable; works on cheap phones.
- **Live Call Companion:** WebSocket streaming; browser speech-to-text; incremental scam-script scoring with escalating warnings; scripted demo scenario rehearsed end-to-end.
- Flywheel: consented Shield checks become de-identified intelligence rows feeding the graph; `shield_checks` telemetry (channel, geo, latency, verdict).
- WhatsApp channel: stub behind an interface (webhook-ready); demo via PWA — don't burn days on Meta business verification.

**Gate G3:** live-call demo works on a phone against a scripted scam call, in Hindi, verdict in-call; check p95 <3s under 100 concurrent users.

## Phase 4 — Terminal v2: Analyst & Officer Experience (4–5 days)
*UX is 15% of judging and carries the whole demo.*

- Rebuild frontend in TypeScript with the design system in `agent/DESIGN_REFERENCE.md` (evolved v1 "Investigator's Terminal" identity: dark command-center, severity color logic, dense-but-legible).
- Views: Overview (live KPIs incl. FP rate + lead time) · FraudScope (intake, review queue, evidence-trace highlighting) · NetworkX (D3 graph w/ campaign lens, temporal scrubber, takedown brief panel) · CrimeMap (choropleth + Shield-density leading-indicator layer) · Evidence Locker (package builder + chain viewer) · Admin (users, metrics, LLM cost).
- Real-time: SSE/WS — new case visibly lands in graph during demo.
- **Campaign Early-Warning:** velocity detector job + banner alerts + projected victim counts.
- Accessibility pass (keyboard nav, contrast); empty/loading/error states everywhere.

**Gate G4:** full demo narrative (`docs/01 §6`) click-through with zero dead ends; officer path complete: alert → brief → 65B evidence export.

## Phase 5 — Scale Proof & Hardening (3–4 days)

- Locust load tests: 500 req/s Shield + 100 req/s intake; publish numbers.
- 100k-case seed; verify graph/map latencies; add missing indexes.
- Observability: structured JSON logs w/ trace IDs, Prometheus metrics + minimal Grafana board (latency, queue depth, LLM cost, FP rate).
- Chaos drills: kill LLM provider (degraded mode works), kill a worker (queue drains), restart Postgres (clean recovery).
- Security suite green (`docs/03 §7`); fix everything found.
- Model eval: 200-case labeled benchmark → precision/recall/FP-rate table for the submission doc.

**Gate G5:** load + chaos + security all green; benchmark table produced.

## Phase 6 — Submission Assets (2–3 days, after product freeze)

- **Demo video** (per hackathon deliverables): follow `docs/01 §6` narrative; ≤5 min; screen capture + phone footage of the live call intercept; script written in Phase 4, only recorded here.
- **Submission document**: problem → solution → architecture diagram (from `docs/02`) → uniqueness (the 5 points in `docs/01 §4`) → metrics table (from G5) → scaling story → roadmap-beyond.
- Presentation deck (hackathon deliverable) from the same material.
- README overhaul: 5-minute quickstart, screenshots, sample data, honest limitations section.
- Full demo playbook execution per `docs/07_DEMO_PLAYBOOK.md` (beat sheet, stat-on-screen rule, fallback recordings, 3 clean rehearsals before recording).

**Gate G6:** a stranger can clone → compose up → run the demo from README alone.

---

## Timeline Summary

| Phase | Focus | Est. |
|---|---|---|
| 0 | Reset, tooling, CI | 1–2 d |
| 1 | Auth, encryption, audit chain | 3–4 d |
| 2 | Async pipeline, pgvector, incremental clustering | 4–5 d |
| 3 | Shield + Live Call Companion | 5–6 d |
| 4 | Terminal v2 UI + early warning | 4–5 d |
| 5 | Load, chaos, security, eval benchmark | 3–4 d |
| 6 | Video, doc, deck, README | 2–3 d |
| **Total** | | **~22–29 days** |

Compression option if the deadline is tight: merge 5 into 4 (do load/security continuously) and demo WhatsApp as mock. Do **not** cut Phase 1 or the Live Call Companion — one is the credibility, the other is the wow. (MudraCheck already dropped by owner decision.)

## Judging-Criteria Coverage Map

| Criterion | Weight | Where we win |
|---|---|---|
| Innovation | 25% | Live call interception, flywheel, 65B-by-construction, early warning |
| Business Impact | 25% | ₹1,776 cr digital-arrest losses; lead-time + FP metrics; NCRP-integration story |
| Technical Excellence | 20% | Async graph pipeline, pgvector, hash chain, provider fallback, eval benchmark |
| Scalability | 15% | Load-test numbers, stateless API, partition/sharding story (`docs/02 §3`) |
| User Experience | 15% | 3-second citizen verdict in 5 languages; command-center Terminal; live graph |
