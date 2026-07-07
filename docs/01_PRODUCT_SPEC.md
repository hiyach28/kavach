# KAVACH v2 — Product Specification

**One-liner:** KAVACH is a fraud-defense operating system for India — it protects citizens *while the scam is happening*, and turns every intercepted attempt into court-ready network intelligence for law enforcement.

**Positioning shift (this is the uniqueness):** v1 was a post-complaint analysis tool, like every other hackathon entry will be. v2 closes the loop: **Shield (citizen, real-time) → Intelligence (analyst, graph) → Takedown (officer, evidence)**. Nobody else will demo intercepting a live digital-arrest call, watching the case appear in the campaign graph, and exporting a Section 65B-ready evidence package — in one continuous flow.

---

## 1. Users

| Persona | Surface | Job to be done |
|---|---|---|
| Citizen (potential victim) | WhatsApp bot / web widget / PWA | "Is this call/message/UPI request a scam? Tell me NOW, in my language." |
| Cybercrime analyst | Investigator's Terminal (web) | Triage complaints, find rings, trace infrastructure |
| Nodal officer / SP | Terminal: Command view | Prioritize districts, approve takedowns, export evidence |
| Bank/telecom partner (future) | REST API | Score a transaction/number against live threat intel |

## 2. Modules

### 2.1 Shield — real-time citizen protection (NEW, flagship)
- **Live Scam Check:** citizen forwards a suspicious message, screenshot, phone number, or UPI ID → verdict in <3s with plain-language explanation in their language (start with 5: Hindi, English, Tamil, Telugu, Bengali; architecture supports 12).
- **Live Call Companion (demo centerpiece):** during a suspicious call, citizen opens the PWA and taps "I'm on a suspicious call." Streaming speech-to-text → incremental scam-script scoring → escalating on-screen warnings ("This matches the CBI digital-arrest script — police NEVER video-call. Hang up.") *before* money moves.
- **Instant lookup:** every check hits the live infrastructure graph — "this number appears in 14 reports across 3 states" is more convincing than any classifier score.
- Every Shield interaction becomes (consented, de-identified) intelligence — the citizen tool *feeds* the analyst graph. This flywheel is the business-impact story.

### 2.2 FraudScope — evidence intake & classification (UPGRADED)
- Keep v1 flow: paste/OCR → de-identify → classify → red flags with citations.
- Add: multi-file intake (screenshots, audio, call recordings, PDFs), batch import (CSV from NCRP helpline 1930), async processing with live status, human review queue with feedback that actually retrains prompts (few-shot store).
- Hardened extraction: dedicated entity extractor for phones / UPI IDs / bank accounts / URLs / Telegram handles / IFSC — not the PII-mask side-effect hack of v1.

### 2.3 NetworkX — campaign intelligence (UPGRADED)
- Keep: infra edges + semantic edges + Louvain campaigns + betweenness takedown briefs.
- Rebuild: pgvector ANN search (no O(n²)), incremental graph updates via worker queue, temporal view (campaign growth animation over time).
- **Campaign Early-Warning (NEW):** velocity detector — when a cluster's report rate accelerates past a threshold, raise a "mass-victimisation in progress" alert with projected victim count. This directly answers the evaluation criterion "detection lead time before mass victimisation."

### 2.4 CrimeMap — geospatial command (UPGRADED)
- Keep choropleth + priority scoring. Add: live Shield-check density layer (leading indicator vs. lagging complaints), campaign-origin overlays, time scrubber, drill to case level.

### 2.5 Evidence Locker — court-admissible packages (NEW)
- Hash-chained (tamper-evident) audit trail for every case from intake to verdict.
- One-click **Intelligence Package export**: campaign summary, entity list with SHA-256 hashes, chain-of-custody log, graph snapshot, auto-drafted **Section 65B(4) certificate** (IT Act) — the "legal admissibility" evaluation criterion, productized.

### 2.6 MudraCheck — DROPPED (owner decision, 2026-07-08)
Counterfeit-currency CV module is out of scope. Do not build, stub, or reference. Listed in `FEATURE_STATUS.md` §Parked.

> Detailed per-feature specifications (IDs F10–F54, acceptance criteria, test modes, demo beats): `docs/04_FEATURE_DETAILS.md`. Datasets and metric definitions: `docs/05_DATA_AND_METRICS.md`.

## 3. Non-Functional Requirements (production bar)

| Area | Requirement |
|---|---|
| Auth | OIDC-style JWT, RBAC (citizen / analyst / officer / admin), per-object audit of every read of PII |
| Privacy | PII envelope-encrypted at rest (AES-256-GCM, per-record DEK); raw identifiers never leave the boundary; LLMs only ever see masked text |
| Integrity | Append-only, hash-chained audit log; evidence exports carry verification hashes |
| Performance | Shield verdict p95 < 3 s; classify enqueue < 200 ms; graph query p95 < 500 ms at 100k cases |
| Scale | Stateless API, queue-backed workers, Postgres + pgvector + Redis; horizontal scaling documented and load-tested to 100 req/s |
| Reliability | LLM fallback chain (primary → secondary model → rules-only degraded mode); no single external dependency can take Shield down |
| Observability | Structured logs, request tracing, metrics dashboard, cost tracking per LLM call |
| I18n | Language detection + response in kind; 5 languages at launch |

## 4. What Makes v2 Unique (say this in the demo)

1. **Point-of-contact interception** — live call companion; everyone else analyzes yesterday's complaints.
2. **The flywheel** — every citizen check enriches the law-enforcement graph; every takedown makes citizen checks smarter.
3. **Court-ready by construction** — hash-chained custody + 65B certificate generation built into the data path, not bolted on.
4. **Early-warning, not post-mortem** — campaign velocity alerts with projected victim counts.
5. **Privacy as architecture** — masked-before-LLM, encrypted-at-rest, hash-only graph. Judges can be told: "the graph never contains a single raw phone number."

## 5. Success Metrics (put these on the dashboard)

- Scam-check verdict latency (p50/p95) · classification precision/recall on a 200-case labeled set · false-positive rate on legitimate messages (<2% target — explicit eval criterion) · campaign detection lead time vs. first-complaint baseline · % of cases linked into campaigns · evidence-package generation time.

## 6. Demo Narrative (build toward this from day one)

1. Live call: volunteer's phone rings with a scripted "CBI officer" — Shield companion flags it in-call, in Hindi, in seconds.
2. The intercepted attempt appears in the Terminal as a new case, auto-linked to an existing 23-case campaign via a shared mule UPI ID.
3. Early-warning banner: campaign velocity spiking, projected 40 victims/week.
4. Officer opens the takedown brief — "seize this account, network fractures 71%" — and exports the 65B evidence package.
5. Close on the CrimeMap showing Shield checks (leading) vs. complaints (lagging), proving the system sees scams before victims report them.
