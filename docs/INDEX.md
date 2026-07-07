# KAVACH v2 — Master Documentation

**Project:** KAVACH — fraud-defense platform for ET AI Hackathon 2026, Problem #6 (AI for Digital Public Safety: fraud, digital-arrest scams, counterfeiting).
**Status:** Planning complete → ready to start Phase 0 of `ROADMAP.md`.

## The idea in 30 seconds
v1 (hackathon build) analyzed fraud complaints *after* victims lost money. v2 keeps v1's genuinely good intelligence core — PII-masked LLM classification, fraud-ring graph clustering, takedown briefs — and rebuilds everything around one loop:

**Shield** (citizen, real-time: "is this call a scam?" answered in-call, in their language)
→ **Intelligence** (analyst: every check and complaint feeds a campaign graph with early-warning velocity alerts)
→ **Takedown** (officer: betweenness-ranked targets + court-ready, hash-chained Section 65B evidence packages)
→ every takedown makes the Shield smarter. That flywheel is the product.

## Document map

| File | What it answers | Read when |
|---|---|---|
| `ROADMAP.md` | 7 phases, gates, timeline (~22–29 dev-days), judging-criteria coverage, 2 standing rules | **Start here** for the plan |
| `FEATURE_STATUS.md` | **Implemented vs pending — the single source of truth.** Feature registry by ID, gate log, parked list | Every session, start AND end |
| `docs/00_ASSESSMENT.md` | Honest audit of the v1 repo — what to keep, what's broken and why | Before touching v1 code |
| `docs/01_PRODUCT_SPEC.md` | v2 modules, users, NFRs, uniqueness claims, demo narrative | Defining any feature |
| `docs/02_ARCHITECTURE.md` | Topology, 7 key design decisions with logic, data model, API, scaling story | Any backend/system work |
| `docs/03_SECURITY.md` | Security checklist mapped to v1 defects + abuse cases + CI gates | Continuously; each gate |
| `docs/04_FEATURE_DETAILS.md` | Elaborate spec per feature (F10–F54): flows, acceptance criteria, test mode, demo beat | Before implementing anything |
| `docs/05_DATA_AND_METRICS.md` | Real datasets (Kaggle/NCRB), synthetic seed generator, benchmark, exact metric formulas, where each live stat appears | Data or metrics work |
| `docs/06_TESTING_AND_STABILITY.md` | Never-break protocol, per-phase regression steps, **API-key conservation policy (mock/replay/live)** | Every phase end; any LLM work |
| `docs/07_DEMO_PLAYBOOK.md` | Demo video beat sheet with timestamps, how every stat gets on screen, fallbacks | Phase 4 onward |
| `agent/CLAUDE.md` | Rules of engagement for Claude sessions (copy to build-repo root) | Every session start |
| `agent/DESIGN_REFERENCE.md` | Tokens, layouts, signature demo moments, accessibility | All UI work |
| `agent/DEV_PROMPTS.md` | Copy-paste prompts per phase; collaboration + recovery prompts | Every session |

**Navigation convention:** everything is cross-referenced by feature ID (F10–F62). A feature's description lives in doc 04, its status in `FEATURE_STATUS.md`, its metrics in doc 05, its tests in doc 06, its demo moment in doc 07 — same ID everywhere.

## Key decisions already made (don't relitigate casually)
1. **Rebuild, not refactor** — v1's SQLite schema, sync pipeline, and repo hygiene aren't salvageable; its concepts and ~5 code assets are (assessment §4).
2. **Postgres + pgvector + Redis workers** — fixes the O(n²)-clustering-in-request-path flaw and gives a real scaling story (architecture §D1–D4).
3. **Shield / Live Call Companion is the flagship** — point-of-contact interception is the uniqueness thesis; it gets Phase 3 entirely and the demo centerpiece slot.
4. **Privacy & admissibility as architecture** — encrypted PII vault, hash-only graph, hash-chained audit, 65B export. These are evaluation criteria, built into the data path.
5. **Scope discipline** — WhatsApp channel stubbed (PWA demos it), **MudraCheck counterfeit module DROPPED entirely**, 5 languages not 12 at launch.
6. **Never break** — `main` always demoable; phase-end regression protocol re-verifies all previous gates (`docs/06 §2`).
7. **API key thrift** — `LLM_MODE=mock` default; tests and CI can never hit the real API; live calls limited to cache-building, rehearsals, and the demo (`docs/06 §3`).
8. **Metrics are shown, not claimed** — model accuracy/FP-rate computed against a versioned benchmark, displayed live in the app, and put on screen in the video (`docs/05`, `docs/07`).

## How to start (developer)
1. Read `ROADMAP.md`, skim the four `docs/` files.
2. Create the new build repo; copy `agent/CLAUDE.md` to its root; copy this planning folder into `docs/planning/`.
3. Open a Claude session, paste the **Session Opener** from `agent/DEV_PROMPTS.md`, and run Phase 0.

## Later-stage deliverables (tracked, not forgotten)
- **Demo video** (≤5 min) — script comes from `docs/01 §6`; produced in Phase 6.
- **Submission document + deck** — skeleton defined in `ROADMAP.md` Phase 6; metrics table produced by the Phase 5 benchmark.
- Hackathon-required: working prototype, architecture diagram (render from `docs/02 §1`), deck, demo video. All covered by gates G5–G6.
