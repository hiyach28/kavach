# ARCHITECTURE.md — KAVACH

## System overview

```
┌─────────────────────────────────────────────────────────────────┐
│                          React Frontend                         │
│   ModuleRail │  FraudScopePage / NetworkXPage / CrimeMapPage    │
│              │        (share CaseContext across all three)     │
└───────────────────────────┬───────────────────────────────────┘
                            │ REST (JSON) — api/client.js
┌───────────────────────────▼───────────────────────────────────┐
│                        FastAPI Backend                         │
│  ┌────────────┐   ┌──────────────┐   ┌─────────────────────┐  │
│  │ FraudScope │   │  NetworkX    │   │     CrimeMap         │  │
│  │  routes    │   │  routes      │   │     routes            │  │
│  └─────┬──────┘   └──────┬───────┘   └──────────┬───────────┘  │
│        │                 │                       │              │
│  deidentify.py     clustering.py         priority_scoring.py    │
│        │                 │                       │              │
│  claude_client.py   (networkx +                  │              │
│        │             python-louvain)              │              │
└────────┼─────────────────┼───────────────────────┼──────────────┘
         │                 │                       │
   Anthropic API      SQLite/Postgres         District mock/NCRB
   (claude-sonnet-4-6)   (single DB,           seed data
                          all tables)
```

## Data flow — one case, start to finish

1. **Submission.** User pastes text into FraudScope. Frontend POSTs to `/classify`.
2. **De-identification.** `deidentify.py` regex-masks phone numbers and 12-digit numeric strings, returns masked text + a token map.
3. **Classification.** `claude_client.py` sends the masked text to Claude with the structured-JSON system prompt (temperature 0.1). Response is logged to `audit_log` *before* validation, so even a failed call is traceable.
4. **Validation.** The response is parsed against the Pydantic schema. Pass → continue. Fail → one retry with a stricter instruction. Fail again → case status set to `needs_manual_review`, still persisted, still gets an `audit_id`.
5. **Persistence.** Case + red flags written to `cases` / `case_red_flags`. Any extracted infrastructure values (phone patterns, UPI handles) are hashed and written to `infra_nodes` / `case_infra_links`.
6. **Graph update.** `clustering.py` checks if the new case shares an infra node with an existing campaign. If yes, it joins that campaign (incremental — no full graph recompute). If no shared infra and no script-similarity match (P2), it becomes its own unclustered node.
7. **Geo aggregation.** If the case has a district, district-level stats are incrementally updated so CrimeMap's next read reflects it (full recompute of `priority_score` for that district only, not the whole map).
8. **Frontend reflects all three.** The active case stays in `CaseContext`; switching to NetworkXPage or CrimeMapPage highlights the same case/campaign/district without the user re-searching.

This is the chain every architectural decision below exists to protect.

## Why these specific technical choices

- **FastAPI over Flask/Django:** async support matters once Claude calls are the bottleneck; auto-generated `/docs` doubles as a judge-facing API reference with zero extra work.
- **SQLite for the hackathon, Postgres-shaped schema from day one:** avoids a rewrite later; see `DATABASE_SCHEMA.md` for the SQL, written to be portable.
- **NetworkX + Louvain over a graph database:** for a dataset this size, an in-memory graph library recomputed incrementally is simpler and faster to ship than standing up Neo4j; revisit only if case volume genuinely reaches a scale where in-memory graph operations become the bottleneck (see scalability roadmap).
- **D3 over a charting library for the graph and map:** force-directed graphs and choropleths with custom interaction (the join animation, the tooltip drill-down) need D3's low-level control — a higher-level chart library would fight you on exactly the two visual moments the demo depends on.

## Scalability roadmap (be explicit about this being a roadmap, not "already done")

| Phase | Trigger | Change |
|---|---|---|
| **Phase 0 — hackathon** | Now | Synchronous classify, full in-memory graph recompute, SQLite, single process |
| **Phase 1 — pilot (one city/state)** | >100 cases/day | Move classification to a background queue (Celery/RQ), websocket push to frontend instead of polling, switch to Postgres |
| **Phase 2 — multi-state pilot** | >1,000 cases/day | Incremental clustering only (recompute touched connected component, not full graph), add Redis cache for district stats, horizontal-scale FastAPI workers behind a load balancer |
| **Phase 3 — production / NCRB integration** | Real ingestion pipeline | Add `pgvector` for script-similarity embeddings, move audit_log to an append-only-enforced store (DB role permissions or a write-once log service), add real auth (officer accounts, role-based access), ingest from real reporting channels instead of manual paste |

State this roadmap explicitly in any pitch — judges consistently reward teams who show they understand *where* their current build will break, over teams who imply it already scales.

## How to proceed (build sequencing)

Follow the priority tiers and time-boxed sprint plan in the build-plan document (`KAVACH_Build_Plan_and_Technical_Deepdive.md`) — that document's P0/P1/P2 split and 6-hour schedule is the canonical build order. In short:

1. Backend skeleton + schema (this doc + `DATABASE_SCHEMA.md`) before any feature code.
2. FraudScope end-to-end (text in → validated structured JSON out → rendered card) before touching NetworkX or CrimeMap — it's the only module that can stand alone as a demo if time runs out.
3. NetworkX with pre-seeded mock data and a static graph before attempting the live-join animation.
4. CrimeMap static choropleth before attempting filters or trend indicators.
5. Cross-links (`CaseContext`, district→campaign count) only after all three modules independently render — wiring links between broken modules wastes time debugging two things at once.
6. Polish, demo rehearsal, fallback-cut decisions per the build-plan's fallback section.
