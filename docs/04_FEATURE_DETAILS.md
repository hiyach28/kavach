# KAVACH v2 — Elaborate Feature Specifications

Every feature has an **ID** (used in `FEATURE_STATUS.md`, commits, and tests), its **phase**, a full description, acceptance criteria (AC), test mode (see `06_TESTING_AND_STABILITY.md` for LLM mock policy), and its **demo beat** (see `07_DEMO_PLAYBOOK.md`).

**MudraCheck (v1 spec §2.6) is DROPPED — decision final. Do not build, stub, or reference it.**

---

## F1x — Platform Core (Phase 1)

### F10 · Authentication & Sessions
JWT login (access 15min / refresh 7d), argon2 hashing, logout revocation via Redis denylist.
- **Flow:** login page → `POST /v1/auth/login` → tokens; silent refresh; 401 → redirect to login.
- **AC:** wrong password = generic error (no user enumeration); 5 failed attempts = 15min lockout; refresh rotation; all tested.
- **Test mode:** pure unit + API tests, no LLM. **Demo beat:** none (implied); mention in doc.

### F11 · RBAC & Jurisdiction Scoping
Roles: `citizen`, `analyst`, `officer`, `admin`. Analysts scoped to district(s)/state; officers to state; admin global.
- **AC:** authz matrix (endpoint × role → expected code) passes 100%; scoped analyst cannot retrieve out-of-jurisdiction case by ID (404, not 403 — no existence leak).
- **Test mode:** API tests. **Demo beat:** D-7 (30s: show analyst vs officer views).

### F12 · PII Vault
AES-256-GCM per-record; DEK wrapped by master key (env). Decrypt endpoint: `officer+` role + mandatory justification string → audit event.
- **Flow:** de-identify produces tokens → originals encrypted to `pii_vault` → main DB stores hashes only.
- **AC:** `pg_dump | grep` on 10 seeded phone numbers finds zero plaintext; decrypt without justification = 422; every decrypt visible in audit viewer.
- **Test mode:** unit tests with test master key. **Demo beat:** D-6.

### F13 · De-identification Engine v2
v1 regexes (phone/Aadhaar/account) + email, PAN, URL, Telegram/WhatsApp handle, IFSC, names via spaCy NER (`en_core_web_sm`, offline). Ordered pipeline, longest-match-first, overlap-safe.
- **AC:** ≥98% recall on a 300-string labeled PII fixture set (build the fixture in Phase 1); zero false tokens on 100 clean strings; runs <50ms per complaint.
- **Test mode:** pure unit, fixture-driven. **Demo beat:** D-2 (masked text shown side-by-side).

### F14 · Hash-Chained Audit Log
Append-only `audit_chain`; `this_hash = SHA256(prev ‖ payload_hash ‖ ts)`; DB role has INSERT-only; `scripts/verify_chain.py`.
- **AC:** verify passes on 10k events; manual UPDATE attempt fails at DB permission level; tampering one row makes verify fail at exactly that seq.
- **Test mode:** unit + DB tests. **Demo beat:** D-6 (chain viewer, live tamper demo on a throwaway copy).

### F15 · API Hardening Layer
Rate limits (Shield 20/min/IP, Terminal 120/min/user), input caps (50KB text, 10MB upload), security headers, strict CORS, error envelope `{success,data,error,trace_id}`, mandatory pagination.
- **AC:** 21st Shield call in a minute → 429 with Retry-After; oversized body → 413; headers verified by test; every list endpoint rejects `limit>100`.
- **Test mode:** API tests. **Demo beat:** none; cite in submission doc.

## F2x — Intelligence Pipeline (Phase 2)

### F20 · Async Case Intake
`POST /v1/cases` validates → masks → vaults → inserts `status=queued` → enqueues → 202 + `case_id` in <200ms. Status machine: `queued → classifying → extracting → linking → clustered | needs_manual_review | failed(reason)`.
- **AC:** enqueue p95 <200ms under 50 concurrent; worker crash mid-job → retry (idempotency key = case_id + stage); poison job → `failed` with reason, never stuck.
- **Test mode:** LLM **mocked**; queue integration test with real Redis in compose. **Demo beat:** D-2 (live status ticker on the case card).

### F21 · LLM Client with Fallback Chain
Provider-agnostic interface: `classify(text) -> Verdict`. Chain: Gemini flash-tier → secondary provider → `RulesOnlyClassifier` (regex + keyword heuristics, marked `degraded=true`). Modes via `LLM_MODE` env: `mock` (default everywhere), `replay` (cached fixtures), `live` (explicit only).
- **AC:** kill primary in test → secondary used, logged; kill both → rules verdict returned, UI shows "degraded" badge; server-side validation rejects out-of-enum fraud_type, out-of-range scores, and evidence strings not present in input (→ retry once → manual review); cost + tokens metered per call.
- **Test mode:** `mock`/`replay` ONLY in tests — see key policy in doc 06 §3. **Demo beat:** D-8 (optional resilience beat).

### F22 · Entity Extraction & Hashed Graph
Dedicated extractor (not the v1 PII-map hack): phones, UPI IDs (`x@bank` pattern list), account+IFSC pairs, URLs/domains, handles. Normalize (E.164, lowercase, strip separators) **then** SHA-256 → `entities` + `case_entity_links`, with `first_seen`, `report_count`.
- **AC:** ≥95% F1 on a 200-case labeled extraction fixture; same number in two formats maps to one entity; report_count increments atomically.
- **Test mode:** pure unit. **Demo beat:** D-3 (entity panel: "seen in 14 reports, 3 states").

### F23 · Embeddings & ANN Similarity
`text-embedding-004` (or provider-equivalent) → `vector(768)` HNSW. `EMBED_MODE` mirrors `LLM_MODE` (mock = deterministic hash-based pseudo-embeddings so clustering is testable offline).
- **AC:** top-k query <50ms at 100k rows; recall@10 ≥0.95 vs brute force on 5k sample.
- **Test mode:** mock embeddings for logic; one small `replay` fixture set (500 pre-computed real embeddings, committed) for realism. **Demo beat:** D-3 (semantic edge appears between cases sharing no infrastructure).

### F24 · Incremental Campaign Clustering
On case link/edge insert: fetch affected connected component (bounded: cap 2,000 nodes, else defer to nightly) → Louvain on subgraph → reconcile campaign IDs (stable-ID rule: largest overlap keeps ID) → recompute takedown brief for changed campaigns only → publish `campaign.updated` event.
- **AC:** processing one new case touches only its component (assert via query counter); results equal full-recluster on 1k-case fixture (ARI ≥0.95); nightly full job reconciles drift.
- **Test mode:** pure algorithmic tests, mock embeddings. **Demo beat:** D-3 (case lands, campaign halo recolors live).

### F25 · Takedown Brief Engine
Per campaign: betweenness centrality per entity node → top target, `pct_connectivity_lost` if removed, ranked top-5 list, cached as JSONB with computed_at.
- **AC:** matches hand-verified values on a 30-node fixture graph; recompute only on campaign change.
- **Test mode:** pure unit. **Demo beat:** D-5 ("seize this UPI ID → network fractures 71%").

### F26 · Batch Import (NCRP/1930-style CSV)
Column-mapped CSV upload → rows become queued cases; per-row error report; used to seed demos and pilots.
- **AC:** 5k-row file imports with progress bar; malformed rows collected, not fatal; idempotent re-upload (dedupe by content hash).
- **Test mode:** mocked LLM. **Demo beat:** D-1 setup (pre-demo seeding, mentioned verbally).

## F3x — Shield (Phase 3)

### F30 · Shield Check API
Decision cascade with per-tier latency budget: (1) entity hash lookup ~5ms → if known-bad, verdict immediately; (2) script-pattern ANN vs campaign centroids ~50ms → high-sim = verdict; (3) LLM ~2s, only if 1–2 inconclusive. Verdict bands only (`danger/suspicious/likely_safe/unknown`) — raw scores never exposed to citizens (anti-probing, doc 03 §6).
- **AC:** p95 <3s live-mode, <300ms when tier 1–2 resolves; verdict + plain-language why + one CTA; every check logged to `shield_checks` (channel, geo-district if consented, latency, tier_resolved).
- **Test mode:** tiers 1–2 fully testable offline; tier 3 mocked. **Demo beat:** D-1.

### F31 · Language Layer
Detect script/language (fasttext lid or heuristic) → respond in kind. Launch: hi, en, ta, te, bn. Verdict copy = reviewed templates with slot-filling (never free LLM generation for citizen-facing text — consistency + safety).
- **AC:** Hindi input → Hindi verdict; template coverage test (every band × language renders); machine-translated strings flagged for human check.
- **Test mode:** pure unit. **Demo beat:** D-1 (Hindi verdict on screen).

### F32 · Citizen PWA
Single screen: paste text / share-target / upload screenshot (client OCR, tesseract.js from v1) / enter number-UPI → verdict card (design doc §3). Installable, <200KB JS budget, works on Android Go class devices.
- **AC:** Lighthouse PWA pass, performance ≥85 mobile; share-target receives WhatsApp forwards; offline shows cached UI + "connection needed" state.
- **Test mode:** component tests + Playwright. **Demo beat:** D-1 (on a real phone, screen-recorded).

### F33 · Live Call Companion — DEMO CENTERPIECE
"I'm on a suspicious call" → mic permission → browser Web Speech API streams transcript over WS → server scores incrementally against scam-script stages (impersonation → threat → isolation → payment demand) → escalating UI states: listening → caution (amber) → DANGER (full-screen red, per design doc §4.1) with stage-specific advice.
- **Stage detection:** keyword+pattern per stage in 5 languages + ANN vs known digital-arrest scripts; LLM used ONLY in live demo mode, throttled to 1 call/15s per session.
- **AC:** scripted demo call triggers caution by ~20s, danger at payment-demand line; works on Chrome Android; total LLM calls in one companion session ≤4; graceful "couldn't hear" state.
- **Test mode:** feed recorded transcript fixtures through the WS pipeline offline — the demo script itself IS a test fixture, rehearsed in CI. **Demo beat:** D-1 (the money shot).

### F34 · Shield→Graph Flywheel
Consented checks become de-identified intelligence: entity hashes join the graph with source `shield`, weight lower than complaints; checks against entities later confirmed in campaigns retroactively strengthen edges.
- **AC:** a Shield check on a mule UPI visibly increments the entity's report_count and can add it to a campaign; consent=false checks store aggregates only.
- **Test mode:** unit + integration, mocked LLM. **Demo beat:** D-4 (intercepted attempt appears in Terminal graph).

## F4x — Terminal & Command (Phase 4)

### F40 · Terminal Shell & Navigation
v1 shell evolved: left module rail, top status bar (env badge, LIVE indicator, degraded-mode badge, user/role), right dossier panel. Keyboard: `g+f/n/m/e/o` jump to modules, `/` global search (case ID, entity fragment, campaign).
- **AC:** every module reachable ≤2 clicks and via keyboard; role hides unauthorized modules; dossier persists across modules.
- **Demo beat:** frames all Terminal beats.

### F41 · Overview Dashboard (real-time stats surface — see doc 05 §4)
Live KPI cards: cases today, active campaigns, **model precision/recall/FP-rate (from continuous eval)**, Shield checks (24h) + p95 latency, early-warning count, LLM cost today. SSE-updated. Each KPI clicks through to its detail.
- **AC:** KPI updates within 5s of underlying event (SSE, no polling); each stat's tooltip explains exactly how it's computed (judge-proofing).
- **Demo beat:** D-7.

### F42 · FraudScope v2
Intake (paste/upload/batch) → live pipeline status → result: verdict card, risk gauge, red flags with **evidence substrings highlighted in the original masked text**, reasoning trace (collapsible), entity panel. Review queue: `needs_manual_review` + low-confidence cases; analyst confirm/correct → correction stored → feeds few-shot store + eval set (doc 05 §3).
- **AC:** highlight offsets exact; corrections change subsequent classifications of near-identical text (few-shot proof test); queue empties correctly.
- **Demo beat:** D-2.

### F43 · NetworkX v2
D3 force graph: case nodes (color = fraud type), entity nodes (shape = type), infra edges solid blue / semantic dashed purple; campaign lens (isolate one campaign); **temporal scrubber** replaying campaign growth; takedown brief slide-in; export subgraph PNG for evidence.
- **AC:** 60fps at 500 visible nodes (canvas renderer, not SVG, above 150 nodes); scrubber replays from case timestamps; new cases arrive via WS with pulse animation (design doc §4.2).
- **Demo beat:** D-3, D-4.

### F44 · Campaign Early-Warning
Worker cron (5min): per campaign compute report-velocity (EWMA of cases+shield-checks/hour); trigger when velocity > 3× baseline AND ≥5 events → alert with projected victims/week (linear + confidence band, assumptions stated in tooltip) → amber banner + optional webhook.
- **AC:** synthetic burst fixture triggers within one cron cycle; quiet campaign never false-triggers across 30-day replay fixture; projection math unit-tested.
- **Demo beat:** D-4 (banner fires during demo via scripted burst).

### F45 · CrimeMap v2
Choropleth (v1 geojson) + layer toggle: complaints (lagging) vs Shield-check density (leading) · campaign origin markers · time scrubber · district drill-down to case list.
- **AC:** layer toggle visibly shows leading-vs-lagging story; drill-down respects jurisdiction scoping; renders <1s at 100k cases (pre-aggregated district_stats table, refreshed by worker).
- **Demo beat:** D-7.

### F46 · Evidence Locker
Campaign → "Build Package": async job assembles case summaries, entity hash list, chain-of-custody segment, graph snapshot PNG, draft Section 65B(4) certificate (template + operator identity + system description), `verify.py` + manifest of SHA-256s → ZIP download; every export audited.
- **AC:** package verifies on a clean machine (`python verify.py` green); tampered file → named in output; export by analyst role → 403.
- **Demo beat:** D-6.

### F47 · Admin Console
Users/roles CRUD, metrics (doc 05 §4), LLM budget controls (daily cap, per-user cap, kill-switch to degraded mode), audit search.
- **AC:** budget cap flip → immediate degraded mode; audit search by case/user/date.
- **Demo beat:** D-8 (optional).

## F5x — Quality & Ops (Phase 5) — see docs 05 & 06
F50 continuous eval harness · F51 load test suite · F52 chaos drills · F53 observability stack · F54 security test suite. Specs live in those docs to avoid duplication; they carry feature IDs so `FEATURE_STATUS.md` tracks them identically.
