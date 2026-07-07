# KAVACH v1 — Honest Assessment of the Existing Project

Repo: `https://github.com/hiyach28/kavach.git` (single squashed commit, ~1,960 lines of app code)
Hackathon target: **ET AI Hackathon 2026 — Problem #6: AI for Digital Public Safety** (fraud, digital arrest scams, counterfeiting)
Judging: Innovation 25% · Business Impact 25% · Technical Excellence 20% · Scalability 15% · UX 15%

---

## 1. What v1 Actually Is

An "Investigator's Terminal" for cybercrime analysts with three modules:

| Module | Function | Implementation |
|---|---|---|
| **FraudScope** | Paste/OCR a complaint → PII-mask → Gemini classifies fraud type, risk score, red flags with MHA/NCRB citations | Regex de-identification → `gemini-2.5-flash` structured output → SQLite |
| **NetworkX** | Fraud-ring graph: cases linked by shared infrastructure + semantic similarity, Louvain campaign clustering, betweenness-centrality "takedown briefs" | `networkx` + `python-louvain` + `text-embedding-004`, D3 force graph |
| **CrimeMap** | District choropleth with priority scoring (NCRB static + live case data) | GeoJSON + weekly stats tables |

Stack: React 19 + Vite + D3 + tesseract.js (client OCR) · FastAPI + SQLAlchemy + SQLite · Gemini API · Docker (backend only).

## 2. What Is Genuinely Good (Keep These)

1. **The core concept chain is strong**: complaint → PII masking → explainable classification → infra hashing → graph clustering → takedown prioritization. This is a real intelligence pipeline, not a CRUD demo.
2. **PII-before-LLM masking** — right instinct, directly relevant to the "auditability / legal admissibility" evaluation focus.
3. **Semantic edges** (linking cases that share *no* infrastructure but identical scam scripts) — v1's most defensible unique idea. Preserve and strengthen it.
4. **Takedown briefs** (betweenness centrality → "block this node, network fractures X%") — turns a graph into an *action*. Judges love this.
5. **Explainability discipline**: reasoning traces, evidence substrings, confidence per flag, audit IDs.
6. Docs culture: `docs/` has contracts, feature status, integration checklist — good bones for agent-assisted development.

## 3. Critical Problems (Why It Is Not Production-Ready)

### Security — severe
- **No authentication or authorization at all.** Every endpoint (cases, PII maps, audit logs) is open. For a law-enforcement platform this is disqualifying.
- **`pii_token_map` stored in plaintext** in SQLite — the "Zero-Leakage PII" claim is false at rest. One file copy leaks every victim's phone/Aadhaar/bank number.
- **No rate limiting, no input size caps, no security headers.** `/classify` is an unauthenticated, unmetered proxy to a paid LLM (cost bomb + prompt injection surface).
- Complaint text goes into the LLM prompt with no injection hardening; LLM output is trusted verbatim.
- Audit log has **no integrity guarantees** (no hash chaining) — not court-admissible, despite that being an explicit evaluation criterion.
- CORS `allow_methods=["*"]`, `allow_headers=["*"]`; silent `except: pass` blocks; no dependency pinning audit.

### Scaling — severe
- **SQLite** single-writer; embeddings stored as JSON strings in a text column.
- **O(n²) cosine similarity across ALL cases + full Louvain recluster runs synchronously inside every `/classify` request.** At ~2,000 cases this means multi-second requests; at 50k (one real district's monthly volume) the system dies. This is the single biggest architectural flaw.
- Synchronous LLM call in the request thread; no queue, no workers, no retry/backoff policy.
- `GET /cases` returns every case unpaginated.
- No migrations (`create_all` on boot), no caching, no horizontal-scale story.

### Engineering hygiene
- **112 MB `.venv/` committed to git** (repo is ~220 MB). Duplicate `Docs/` and `docs/` trees. Empty `.env.example`.
- README links to `docs/TRY_KAVACH.md` and sample cases that don't exist.
- Tests exist but are thin; no CI; frontend Dockerfile present but commented out of compose.
- Single git commit — no history to learn from.

### Product gaps vs. the problem statement
- Entirely **reactive**: helps after a complaint is filed. The problem statement demands detection "at the point of contact rather than the point of complaint" and "lead time before mass victimisation."
- **No citizen-facing surface** (the statement names WhatsApp/IVR/app in 12 regional languages).
- No counterfeit-currency component (optional, but it's in the problem title).
- English-only. No live/streaming detection. No inter-agency intelligence package export.

## 4. Verdict

**Keep the concept and the graph-intelligence core. Rebuild the platform around it.**
The three-module idea survives; the persistence layer, security model, processing pipeline, and scope must be rebuilt. Reuse: prompt/schema design, de-identification logic (as one layer of several), Louvain/centrality logic (made incremental + async), D3 graph and design-language ideas from the frontend. Discard: SQLite schema-as-is, synchronous pipeline, the committed venv, duplicate docs.

See `ROADMAP.md` for the rebuild plan and `docs/01_PRODUCT_SPEC.md` for what v2 becomes.
