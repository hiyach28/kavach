# FEATURE_REQUIREMENTS.md — KAVACH

Status legend: `[MVP]` required for the core demo chain, `[P1]` strongly recommended, `[P2]` stretch. This maps to the tiers in the build-plan doc — keep both in sync if scope changes.

## Module 1 — FraudScope

| # | Requirement | Tier |
|---|---|---|
| 1.1 | User can paste free text (call transcript, message, UPI request) into a single input | MVP |
| 1.2 | System de-identifies phone numbers and 12-digit numeric (Aadhaar-like) patterns before sending to Claude | MVP |
| 1.3 | System returns a structured verdict: fraud_type, risk_score (0-100), confidence, red_flags[], verdict, reporting_portal, audit_id | MVP |
| 1.4 | Invalid/malformed LLM responses degrade gracefully to `needs_manual_review` rather than erroring | MVP |
| 1.5 | Result renders as a card: risk score ring, verdict banner, list of red flags color-coded by severity | MVP |
| 1.6 | Matched evidence phrases are visually underlined inline in the original pasted text, color-coded by severity | P1 |
| 1.7 | "Report this" button deep-links to the correct government reporting portal | P1 |
| 1.8 | Officer can mark a result "confirmed" or "false positive" (feedback loop, stored not yet acted on) | P2 |
| 1.9 | Classification latency displayed to the user (supports the "<2s" performance claim) | P2 |

**Acceptance criteria for 1.3:** Given a known digital-arrest script, the system returns `fraud_type: "digital_arrest"`, at least 3 red flags with non-empty `evidence` fields that are substrings of the input, and a `risk_score` ≥ 70.

## Module 2 — NetworkX

| # | Requirement | Tier |
|---|---|---|
| 2.1 | Database is pre-seeded with ≥15 mock cases forming exactly 3 visually distinct campaigns | MVP |
| 2.2 | Graph renders as a D3 force-directed layout, nodes colored by campaign, sized by degree | MVP |
| 2.3 | New FraudScope submissions that share infrastructure with an existing campaign are added to the graph and visually join that cluster | MVP |
| 2.4 | Clicking a case node opens a detail panel showing that case's FraudScope output | P1 |
| 2.5 | New-node addition is animated (scale + color transition) rather than an instant re-render | P1 |
| 2.6 | A second edge type based on text/script similarity (embedding distance) links cases that share no infrastructure but reuse the same script | P2 |
| 2.7 | Campaign cards summarize case count and total estimated financial loss per cluster | P1 |
| 2.8 | **Takedown Brief**: for each campaign, compute betweenness centrality on the infra-node projection and surface the single highest-value target node (the "bridge" holding sub-rings together), not just a flat list of equally-weighted nodes | MVP |
| 2.9 | Takedown Brief includes a quantified collapse-impact figure: % of case-to-case connectivity lost and whether the network fractures into more isolated sub-rings if the top target is removed | MVP |
| 2.10 | Takedown Brief flags cross-jurisdiction campaigns (cases spanning >1 district) for escalation above local-station level | P1 |
| 2.11 | "Export Brief" produces a structured summary (campaign id, ranked targets + recommended action, collapse impact, evidence case ids, total loss) suitable for handing to an investigating officer | P1 |

**Why 2.8-2.9 are MVP, not P1:** this is the feature that justifies NetworkX existing as a module at all. Without it, the graph is a visualization with no decision attached — judges and real users will ask "what do I do with this" the moment they see a node graph, and a ranked, quantified target is the only credible answer. See `network_intelligence.py` for the reference implementation and a worked example showing a master account bridging two phone-spoof sub-groups that a flat cluster view would hide.

**Acceptance criteria for 2.8-2.9:** given a campaign where one infra node connects two otherwise-disconnected sub-groups of cases (as in the `network_intelligence.py` demo), the system must rank that node first by betweenness centrality, and `collapse_impact` must report `fractures_network: true` with `pct_connectivity_lost` > 0 — a campaign with no bridging structure (e.g. a single infra node shared by all cases, no sub-groups) is expected to show a high `case_reach` target but no fracture.

**Acceptance criteria for 2.3:** Submitting a case containing an infrastructure value (e.g. a UPI handle) already present in a seeded campaign results in that case's node appearing connected to that campaign within one page refresh, with no manual intervention.

## Module 3 — CrimeMap

| # | Requirement | Tier |
|---|---|---|
| 3.1 | India district-level choropleth renders using a public district GeoJSON | MVP |
| 3.2 | Each district has a computed priority_score (0-100) from the documented weighted formula | MVP |
| 3.3 | Hovering a district shows complaint_count, estimated_loss, and priority_score in a tooltip | MVP |
| 3.4 | District tooltip also shows count of active NetworkX campaigns originating in that district | P1 |
| 3.5 | User can filter the map by fraud type | P2 |
| 3.6 | District detail includes a simple trend indicator (rising/falling vs prior week) | P2 |
| 3.7 | "Export enforcement brief" produces a printable/PDF-style summary for a selected district | P2 |

**Acceptance criteria for 3.2:** Given mock data for at least 10 districts with varying complaint counts and growth rates, the top-ranked district by priority_score is verifiably the one with the highest combination of volume, growth, and impact per the documented formula — not just the highest raw complaint count.

## Cross-cutting / platform requirements

| # | Requirement | Tier |
|---|---|---|
| C.1 | A case selected in any module remains the active context when navigating to another module | MVP |
| C.2 | Every classification (success or failure) is persisted with a unique audit_id and timestamp | MVP |
| C.3 | No raw PII is ever sent to the Claude API or stored unmasked alongside case records | MVP |
| C.4 | Severity is communicated with both color and an icon/label, not color alone | P1 |
| C.5 | System status bar shows live counts: total cases, active campaigns, top-priority district | P1 |
| C.6 | Audit log is viewable (even as a simple table) for any case by its audit_id | P2 |

## Non-functional requirements

- **Performance:** classification round-trip under 3 seconds for the demo; graph and map renders under 1 second for the seeded mock dataset sizes.
- **Reliability:** a malformed or unexpected LLM response must never crash the request — always degrade gracefully.
- **Accessibility:** severity indicators colorblind-safe (color + icon); keyboard-navigable module switching; visible focus states.
- **Security:** no secrets in source control; PII masking is non-bypassable by any code path that calls the LLM.
- **Auditability:** every inference traceable by audit_id, including failed/degraded ones.