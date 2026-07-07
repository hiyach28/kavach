# KAVACH v2 — System Architecture & Scaling Design

## 1. Topology

```
 Citizen (PWA / WhatsApp)          Analyst / Officer (Terminal SPA)
        │                                   │
        ▼                                   ▼
 ┌─────────────────────────────────────────────────┐
 │  API Gateway (FastAPI, stateless, N replicas)   │
 │  authn(JWT) · RBAC · rate-limit · input caps    │
 └──────┬──────────────────────┬───────────────────┘
        │ fast path (<3s)      │ enqueue (<200ms)
        ▼                      ▼
 ┌──────────────┐      ┌──────────────────┐
 │ Shield svc   │      │  Redis (queue +  │
 │ lookup→LLM   │      │  cache + pubsub) │
 └──────┬───────┘      └───────┬──────────┘
        │                      ▼
        │              ┌──────────────────────────────┐
        │              │ Workers (arq/Celery, scale-N)│
        │              │ • classify (LLM)             │
        │              │ • embed → pgvector           │
        │              │ • entity-extract → graph     │
        │              │ • incremental recluster      │
        │              │ • early-warning scan (cron)  │
        │              │ • evidence-package builder   │
        │              └───────┬──────────────────────┘
        ▼                      ▼
 ┌─────────────────────────────────────────────────┐
 │ PostgreSQL 16 + pgvector                        │
 │ cases · entities · edges · campaigns · users    │
 │ audit_chain (append-only) · encrypted PII vault │
 └─────────────────────────────────────────────────┘
        │ SSE/WebSocket via Redis pub/sub
        ▼
   Live UI updates (new case lands in graph in real time)
```

External: LLM providers behind a **provider-agnostic client** (primary: Gemini flash-tier for speed/cost; fallback: second provider; final fallback: rules-only regex+heuristic verdict so Shield never goes dark). Speech-to-text for Live Call Companion (browser Web Speech API for demo; server STT as upgrade path).

## 2. Key Design Decisions & Logic

### D1. Everything heavy is async
`/classify` only: validate → mask → encrypt PII → insert case (`status=queued`) → enqueue → return case_id. Workers do LLM, embedding, extraction, clustering. UI subscribes to case channel for progress. *Why:* v1 ran an O(n²) similarity pass + Louvain inside the request — the #1 scalability defect.

### D2. Shield is a separate fast path
Shield checks are latency-critical and mostly read-only: (1) exact entity lookup in the graph (indexed hash lookup, ~ms — "seen in 14 reports" beats any model), (2) cached script-pattern match (pgvector ANN against known scam-script centroids), (3) LLM only if steps 1–2 are inconclusive. Cache verdicts per entity-hash with TTL. *Why:* meets <3s p95 and survives LLM outages.

### D3. Postgres + pgvector replaces SQLite + JSON embeddings
- `cases.embedding vector(768)` with HNSW index → top-k similar cases in ms, replaces the all-pairs cosine loop.
- Graph stored relationally (`entities`, `case_entity_links`, `semantic_links`) — at this scale a dedicated graph DB is unnecessary complexity; NetworkX in workers operates on the *affected subgraph only*.
- Alembic migrations from day one.

### D4. Incremental clustering
On new case: find neighbors (shared entities + ANN top-k > threshold) → load only the connected component(s) touched → run Louvain on that subgraph → merge/split campaigns as needed. Full recluster is a nightly cron job, not a request-path operation. Centrality/takedown briefs computed per-campaign on change, cached on the campaign row.

### D5. PII vault (fixes v1's plaintext token map)
- `pii_vault(id, case_id, token, ciphertext, dek_wrapped, created_at)` — AES-256-GCM per record, DEK wrapped by a master key from env/KMS.
- Decryption requires `officer+` role, logs a `pii_access` audit event with justification text. The main DB and graph carry **only SHA-256 hashes** of identifiers.

### D6. Hash-chained audit (court admissibility)
`audit_chain(seq, case_id, event, payload_hash, prev_hash, this_hash, ts)` where `this_hash = SHA256(prev_hash ‖ payload_hash ‖ ts)`. Append-only (no UPDATE/DELETE grants). Evidence packages embed the chain segment + verification instructions; a bundled `verify.py` recomputes the chain.

### D7. LLM hardening
- Complaint text wrapped in delimited untrusted-content blocks; system prompt instructs to treat it as data.
- Structured output enforced (schema), then **validated server-side** (enums, ranges, evidence substrings must exist in input) — never trust model output.
- Per-user and global token budgets; cost metering per call written to metrics.

## 3. Scaling Story (tell the judges)

| Load | Configuration |
|---|---|
| Demo / pilot (1 district) | docker-compose: 1 API, 2 workers, Postgres, Redis |
| State (≈50k cases/mo) | k8s/ECS: 3× API, 6× workers, managed Postgres w/ read replica, Redis cluster |
| National (NCRP-scale, ~1.1M complaints/yr) | Partition `cases` by month; per-state campaign sharding (fraud rings are natural graph partitions with rare cross-state edges handled by a reconciliation job); queue-based backpressure; CDN for static UI |

Statelessness of API + idempotent workers means scaling = replicas. Load test with Locust at 100 req/s classify + 500 req/s Shield checks; publish the numbers in the demo doc.

## 4. Data Model (core tables)

`users`(role, district_scope) · `cases`(status, fraud_type, risk, confidence, embedding, campaign_id, district, language) · `red_flags` · `entities`(type, value_hash, first_seen, report_count) · `case_entity_links` · `semantic_links`(a, b, score) · `campaigns`(label, velocity, projected_victims, takedown_brief jsonb) · `pii_vault` · `audit_chain` · `shield_checks`(channel, verdict, latency_ms, geo) · `evidence_packages`.

## 5. API Surface (v2)

```
POST /v1/auth/login                         → JWT
POST /v1/shield/check          (citizen)    → verdict <3s
WS   /v1/shield/live           (citizen)    → streaming call companion
POST /v1/cases                 (analyst)    → 202 + case_id (async)
GET  /v1/cases?page=&filter=   (analyst)    → paginated
GET  /v1/cases/{id}/events     (SSE)        → processing progress
GET  /v1/graph/campaigns/{id}  (analyst)    → subgraph + brief
GET  /v1/map/districts?window= (officer)
POST /v1/evidence/{campaign}   (officer)    → 65B package (async)
GET  /v1/admin/metrics         (admin)
```
Versioned, paginated, consistent envelope `{success, data, error, trace_id}`.

## 6. Repo Layout (rebuild)

```
kavach/
├── backend/            FastAPI app (api/, workers/, core/, models/, services/, tests/)
├── frontend/           Terminal SPA (React + Vite + TS)
├── shield-pwa/         Citizen PWA (or /shield route in frontend — decide Phase 3)
├── infra/              docker-compose.yml, k8s notes, locustfile.py
├── docs/               this folder
├── agent/              CLAUDE.md, prompts, design reference
└── .github/workflows/  ci.yml (lint, test, build)
```
