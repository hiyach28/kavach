# KAVACH — Technical Deep Dive & 6-Hour Build Plan

**AI Digital Safety Intelligence Platform**
*Predict, detect, and dismantle digital fraud networks — before mass victimisation, not after.*

---

## 1. Executive Summary

KAVACH is pitched as three connected intelligence modules rather than a single chatbot:

| Module | Function | Core Tech |
|---|---|---|
| **FraudScope** | Classifies a single piece of suspicious content (call transcript, message, UPI request) into a fraud type with cited evidence | Claude API, structured JSON output |
| **NetworkX** | Clusters multiple FraudScope cases into fraud rings/campaigns using shared infrastructure | Graph theory, community detection |
| **CrimeMap** | Aggregates cases geospatially to rank districts for enforcement deployment | Geospatial scoring, choropleth viz |

The pitch's strength is the **chain**: a single case (FraudScope) becomes part of a network (NetworkX) which becomes a geographic enforcement signal (CrimeMap). Judges should see one case flow through all three modules live. That chain is the actual product — not any one module in isolation. Everything in this plan is built around protecting that end-to-end chain even if individual modules get less polish.

This document expands the original 10-hour plan into a **6-hour plan**, since real hackathon time is almost always shorter than the ideal estimate. It is built so that **if you stop at any checkpoint, what exists already works as a demo** — nothing is left half-wired.

---

## 2. Module Deep Dives

### 2.1 FraudScope — Classification Engine

**What it actually does, step by step:**

1. User pastes raw text (call transcript, WhatsApp message, UPI request, SMS).
2. Backend strips obvious PII (phone numbers, Aadhaar-like numeric patterns) and replaces with placeholder tokens (`[PHONE_1]`, `[ID_1]`) before the text ever reaches the LLM. The real values are stored separately, keyed to a case ID.
3. The de-identified text is sent to the Claude API with a system prompt that forces a strict JSON schema response (fraud type, risk score, confidence, a list of red flags each tied to an evidence phrase, a plain-language verdict, and a reporting portal URL).
4. The JSON response is validated against a schema (Pydantic on the backend) before it's trusted — if Claude returns malformed JSON, the system retries once with a stricter instruction, then falls back to a "needs manual review" state rather than crashing.
5. The validated case is written to the database and simultaneously emitted as a node to the NetworkX graph (see 2.2).

**Why this is more defensible than "just a scam-text classifier":**
- The output is **typed and structured**, not a paragraph of prose — this is what makes it auditable. A police officer or judge can point to `flag_id: AUTH_IMP_001` and the exact evidence phrase.
- Each red flag carries its own category (critical/high/medium) so the system can show *why* it reached a verdict, not just the verdict.
- Because the schema includes an `audit_id`, every classification is permanently traceable — this directly answers "how is this legally usable" before a judge asks.

**The 6 fraud types and why these 6 specifically:** digital arrest, UPI spoofing, OTP/SIM-swap, investment fraud (including pig-butchering style schemes), job/loan advance-fee scams, and courier/parcel seizure scams. These are chosen because they cover the overwhelming majority of reported cybercrime complaint volume in India and they share a detectable linguistic structure (authority claim → urgency → isolation → payment demand), which is exactly what the red-flag taxonomy below is built to catch.

**The red-flag taxonomy (what the model is instructed to look for):**

| Flag | Severity | What it catches |
|---|---|---|
| Authority impersonation | Critical | Claims to be CBI/ED/Customs/TRAI/police |
| Urgency + arrest threat | Critical | "Arrested in 2 hours", "warrant issued" |
| Secrecy demand | High | "Don't tell anyone", "confidential investigation" |
| Payment under pressure | Critical | UPI/crypto demand with a countdown |
| Spoofed identity signals | Medium | Fake case/badge numbers, doctored documents |
| Abnormal channel usage | Medium | Government agency "calling" over WhatsApp/personal UPI |

**Demo moment that sells this module:** paste a real (anonymised) digital-arrest script. Get a response in under 2 seconds with 4 flags highlighted and a pre-filled reporting-portal link. The visual payoff is the red-flag list lighting up against the pasted text, not the JSON itself — the JSON is the backend; the UI needs to *visually underline or highlight* the matched evidence phrases inside the original text for this to land with judges.

---

### 2.2 NetworkX — Graph Intelligence Layer

**The core idea:** one complaint is a data point. Ten complaints sharing the same phone number pattern, same mule account, or same device fingerprint is a *prosecutable network*. This module's entire job is making that shared infrastructure visible.

**How a case becomes a graph:**
- Every FraudScope case creates a `case` node.
- Any entity extracted from the case (a phone number pattern, a UPI handle, a bank account fragment, a device ID if available) becomes an `infrastructure` node.
- An edge is drawn between a case and each infrastructure node it touches.
- When two cases share an infrastructure node, they are implicitly linked through it — this is what visually shows up as a "ring" instead of an isolated dot.

**Clustering logic:** once you have a graph of cases and infrastructure nodes, run a community-detection algorithm (Louvain method, available in `python-louvain` or `networkx.algorithms.community`) on the case-to-case projection (two cases are connected if they share ≥1 infrastructure node, edge weight = number of shared nodes). Each detected community is a "campaign." Campaign size and total estimated financial loss become the headline numbers shown on the graph.

**What makes the live demo work:** pre-seed the database with ~15-20 mock cases that already form 3 visually distinct clusters (so the graph looks meaningful even before you do anything). Then, live, submit one *new* case through FraudScope that shares an infrastructure node with one existing cluster, and show it animate into that cluster on the graph. This single animation is the most convincing 15 seconds of the entire demo — prioritise this over graph polish.

**Visualization notes:** D3 force-directed graph, node radius scaled by campaign size, node colour by campaign ID, edge thickness by shared-infrastructure-count. Clicking a node should open a small side panel with the case's FraudScope output (this is the cross-module link judges are told to look for).

---

### 2.3 CrimeMap — Geospatial Enforcement Layer

**The core idea:** most dashboards stop at "here is where crime happens." CrimeMap's job is to answer "where should officers go *this week*."

**Priority scoring formula (transparent, judge-explainable):**

```
priority_score = (complaint_volume_normalized * 0.4)
                + (week_over_week_growth_rate * 0.35)
                + (estimated_financial_impact_normalized * 0.25)
```

Each district gets a 0–100 composite score from this formula. This is intentionally a simple, explainable weighted sum rather than a black-box model — when a judge asks "how did you rank this district above that one," you want a one-line answer, not "the model decided."

**Data:** since live NCRB district-level data isn't realistically pullable in a hackathon window, use NCRB 2023 published cybercrime statistics as the seed distribution and generate synthetic but statistically plausible week-over-week deltas on top of it. Be upfront in the demo that this is "seeded with NCRB 2023 patterns" — that's an honest and still impressive answer.

**What ties it back to the other modules:** when a district is selected, its tooltip should pull and show: total complaints, estimated ₹ loss, and **the number of active NetworkX campaigns whose cases originate in that district**. This is the second (and last) cross-module link you need to nail live.

---

## 3. MVP Definition

The MVP is **not** "all three modules at full fidelity." The MVP is **the smallest version of the full chain that still proves the core idea**: one case flows from text → classification → graph cluster → map signal.

**MVP = the following and nothing more:**
1. A text box that sends input to Claude and renders the structured JSON as a readable card (FraudScope, minimal UI).
2. A pre-seeded graph (NetworkX) with 3 visible clusters, and the ability for one new case to join a cluster live.
3. A static choropleth (CrimeMap) with at least the priority score and one tooltip stat, no filters needed yet.
4. The two cross-links: case → graph cluster, and district → campaign count.

Everything beyond this (filters, animations, audit log UI, demo polish, deploy pipeline) is enhancement layered on top of a working MVP — never built before the MVP works end-to-end.

---

## 4. Priority Tiers

Work is split into **P0 (must exist for any demo to work)**, **P1 (makes the demo good)**, and **P2 (makes the demo impressive)**. If time runs out, you stop at the end of a tier, not mid-task — every task below is sized to be independently completable.

| Tier | Item | Module |
|---|---|---|
| **P0** | FastAPI backend skeleton + DB schema (cases, entities, edges) | Core |
| **P0** | Claude API call returning validated structured JSON | FraudScope |
| **P0** | Minimal React form + result card rendering JSON | FraudScope |
| **P0** | Mock data: 15-20 pre-seeded cases forming 3 clusters | NetworkX |
| **P0** | Static D3 force graph rendering pre-seeded clusters | NetworkX |
| **P0** | Priority score formula computed on mock district data | CrimeMap |
| **P0** | Static D3 choropleth rendering priority scores | CrimeMap |
| **P1** | Live case → graph cluster animation on submit | NetworkX |
| **P1** | Red-flag evidence highlighting inside pasted text | FraudScope |
| **P1** | District tooltip showing linked campaign count | CrimeMap |
| **P1** | Node click → case detail side panel | NetworkX |
| **P2** | Audit log viewer page | Core |
| **P2** | Filter by fraud type on map | CrimeMap |
| **P2** | Dashboard landing page with aggregate metrics | Core |
| **P2** | Deploy + polish (favicon, loading states, demo video) | Core |

---

## 5. 6-Hour Sprint Plan

| Time | Block | Goal | Tier covered |
|---|---|---|---|
| 0:00 – 0:30 | **Scaffold** | Repo, FastAPI skeleton, React boilerplate, DB schema written to file (don't migrate yet) | P0 |
| 0:30 – 1:30 | **FraudScope backend** | Claude API integration, JSON schema enforced, Pydantic validation, one working `/classify` endpoint tested via curl/Postman | P0 |
| 1:30 – 2:15 | **FraudScope frontend** | Text box → result card. Make the result card look good now; it's the most-shown screen | P0 |
| 2:15 – 2:30 | **Checkpoint** | If FraudScope works end-to-end, you have a demoable product. Do not proceed until this is true | — |
| 2:30 – 3:30 | **NetworkX mock data + static graph** | Write 15-20 seeded cases with deliberate shared infrastructure, render with D3 force layout, colour by cluster | P0 |
| 3:30 – 4:00 | **NetworkX live linking** | Wire new FraudScope submissions to also write to the graph + trigger the join animation | P1 |
| 4:00 – 4:45 | **CrimeMap static** | District priority formula on mock NCRB-seeded data, render choropleth, one tooltip stat | P0 |
| 4:45 – 5:00 | **Checkpoint** | All three modules individually demoable. If short on time, stop building features and move straight to polish | — |
| 5:00 – 5:20 | **Cross-links** | District tooltip → campaign count; graph node click → case detail panel | P1 |
| 5:20 – 5:45 | **Polish pass** | Loading states, consistent styling, fix the worst visual bugs, write 3-line architecture note | P2 |
| 5:45 – 6:00 | **Demo run-through** | Practice the actual click path you'll use live, twice. This catches more bugs than more coding would | — |

**Golden rule:** never start a new feature with less than 30 minutes left in its block. If a block's goal isn't done at its time-box, downgrade it (e.g., skip the animation, keep the static graph) and move on. A finished P0 demo beats an unfinished P1 feature every time.

---

## 6. Fallback Plan If Time Runs Short

If you're behind schedule at the 3-hour mark, cut in this order (reverse of priority):
1. Drop the live-join animation — show the pre-seeded clustered graph as static, narrate the concept verbally.
2. Drop map filtering and the dashboard landing page entirely.
3. Drop the audit log viewer — mention the `audit_id` field already exists in the JSON output as your "auditability" answer; you don't need a UI for it to be true.
4. If FraudScope itself isn't done by hour 2, that becomes the *entire* demo — a sharp, well-explained single module beats three broken ones.

---

## 7. Prompts for AI Coding Assistants

Use these as direct prompts to Claude Code (or similar) — each is scoped to one P0 task so it can be completed and verified independently.

### 7.1 Backend scaffold
```
Set up a FastAPI backend for a fraud-intelligence app called KAVACH.
Requirements:
- SQLite via SQLAlchemy for now (swappable to Postgres later)
- Models: Case (id, raw_text_deidentified, fraud_type, risk_score,
  confidence, verdict, reporting_portal, audit_id, district, created_at),
  RedFlag (id, case_id FK, flag_id, category, evidence, explanation),
  InfraNode (id, type, value_hash), CaseInfraLink (case_id, infra_node_id)
- CORS enabled for localhost:3000
- A /health endpoint
- Folder structure: app/main.py, app/models.py, app/schemas.py, app/routes/
Give me the full file contents, not snippets.
```

### 7.2 FraudScope classification endpoint
```
In the FastAPI app, add a POST /classify endpoint that:
1. Accepts {"text": string}
2. Runs simple regex-based PII de-identification on phone numbers and
   12-digit numeric strings (Aadhaar-like), replacing with [PHONE_n]/[ID_n]
   tokens, and returns the mapping separately (don't send raw PII to Claude)
3. Calls the Anthropic API (model claude-sonnet-4-6) with this system prompt:
   "You are KAVACH FraudScope, an Indian cybercrime intelligence classifier.
   Respond ONLY with valid JSON matching this schema, no markdown, no preamble:
   {fraud_type: one of [digital_arrest, upi_spoofing, otp_sim_swap,
   investment_fraud, job_loan_scam, courier_parcel, legitimate],
   risk_score: int 0-100, confidence: float 0-1,
   red_flags: [{flag_id, category: critical|high|medium, evidence, explanation}],
   verdict: string, reporting_portal: url, audit_id: uuid}"
4. Validates the response against a Pydantic model; if invalid, retry once
   with an added instruction "Your last response was invalid JSON. Return
   ONLY the JSON object."; if it fails twice, return a 200 with
   {"status": "needs_manual_review"}
5. On success, writes the Case + RedFlags to DB and returns the full object
Use temperature 0.1. Include error handling for API timeouts.
```

### 7.3 FraudScope result card (React)
```
Build a React component FraudScopeResult that takes a JSON object matching
this shape: {fraud_type, risk_score, confidence, red_flags: [{flag_id,
category, evidence, explanation}], verdict, reporting_portal, audit_id}.
Design requirements:
- Risk score shown as a large number with a colour-coded ring (green <30,
  amber 30-70, red >70)
- Red flags listed as cards, colour-dotted by category (critical=red,
  high=amber, medium=green), each showing the evidence phrase in monospace
  quote styling and the explanation beneath it
- Verdict shown as a one-line banner above the flags
- A "Report this" button linking to reporting_portal
- audit_id shown small and grey at the bottom, labelled "Audit ID"
Use Tailwind core utility classes only, no external UI library.
```

### 7.4 NetworkX mock graph + clustering
```
Write a Python script that:
1. Generates 18 mock fraud cases across 3 distinct campaigns. Each campaign
   shares 2-3 infrastructure nodes (a phone-pattern, a UPI handle, a device
   id) across its cases; cases in different campaigns share nothing.
2. Builds a networkx Graph with case nodes and infra nodes, edges between
   a case and the infra nodes it touches.
3. Projects this onto a case-to-case graph (edge if cases share ≥1 infra
   node, weight = number of shared infra nodes).
4. Runs Louvain community detection (use python-louvain) on the projected
   graph and assigns each case a campaign_id.
5. Exports the full graph (all nodes + edges + campaign_id + node type) as
   JSON in a shape ready for D3 force-directed rendering: {nodes: [{id,
   type, campaign_id, label}], links: [{source, target, weight}]}
Print the JSON to a file graph_seed.json.
```

### 7.5 D3 force graph (React/HTML)
```
Build an HTML+D3 (d3 v7) force-directed graph component that:
- Loads a JSON of {nodes: [{id, type, campaign_id, label}], links:
  [{source, target, weight}]}
- Colours nodes by campaign_id (use a fixed palette of 4-5 distinct colours)
- Sizes case nodes by their degree (more connections = bigger), infra
  nodes stay small and grey
- Edge thickness proportional to weight
- On node click, calls a passed-in onNodeClick(nodeId) callback
- Supports an addNode(newNode, newLinks) function that adds a node with
  a brief scale-up + colour transition animation, and re-runs the force
  simulation so it settles into its cluster
Keep this as a single self-contained file using D3's standard force
simulation (forceManyBody, forceLink, forceCenter, forceCollide).
```

### 7.6 CrimeMap choropleth + priority scoring
```
Build a Python function compute_priority_score(district_data) where
district_data is a list of {district, state, complaint_count,
prior_week_complaint_count, estimated_loss_inr}. Compute, per district:
- complaint_volume_normalized = min-max normalized complaint_count
- growth_rate = (complaint_count - prior_week_complaint_count) /
  max(prior_week_complaint_count, 1), then min-max normalized
- impact_normalized = min-max normalized estimated_loss_inr
- priority_score = volume*0.4 + growth_rate*0.35 + impact_normalized*0.25,
  scaled to 0-100
Return a list sorted descending by priority_score.
Then build a D3 v7 choropleth using a provided India districts GeoJSON,
colouring each district by priority_score (sequential colour scale,
light yellow to dark red), with a tooltip on hover showing district name,
complaint_count, estimated_loss_inr formatted as ₹X Cr, and priority_score.
```

### 7.7 Cross-module link: district → campaign count
```
Add a FastAPI endpoint GET /district/{district_name}/summary that returns
{district, complaint_count, estimated_loss_inr, priority_score,
active_campaign_count}, where active_campaign_count is the number of
distinct campaign_ids (from the NetworkX clustering output) whose cases
have case.district == district_name. Wire this into the CrimeMap tooltip
so hovering a district shows this live count instead of a static number.
```

---

## 8. One-Line Pitch Reminders for the Demo

- FraudScope: *"This isn't a scam detector that says yes or no — it tells you exactly which phrase triggered the alert and where to report it."*
- NetworkX: *"Ten isolated complaints become one prosecutable network the moment they share infrastructure — watch this new case snap into an existing ring."*
- CrimeMap: *"We don't just show where fraud happened — we rank where police should go this week, and why, in one transparent formula."*

Keep the demo narrative anchored to **one case walking through all three modules**. That throughline is what separates KAVACH from "three separate hackathon projects glued together."
