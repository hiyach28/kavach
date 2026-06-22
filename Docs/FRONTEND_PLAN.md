# FRONTEND_PLAN.md — KAVACH

## Design thesis

KAVACH is an investigator's terminal, not a chat assistant. Every screen should read like an analyst console used by someone who works cybercrime cases daily — calm, dense with real information, and quiet about the fact that an LLM is involved at all. The product loses its core pitch ("not a chatbot") the moment its UI looks like one. No centered chat column, no message bubbles, no "thinking…" shimmer, no rounded gradient cards — those are the visual tells of "AI demo," and the entire differentiation argument in the pitch deck depends on not having them.

The three things this design must never look like: (1) a generic SaaS landing page with a hero gradient and a chatbot widget, (2) a dark "hacker" theme with neon-on-black for its own sake, (3) a templated admin dashboard kit. The reference world this should actually draw from: case-management software, NOC/SOC monitoring consoles, redacted case-file documents, air-traffic-style status boards — tools built for people doing serious, attentive work, not consumer apps.

## Design tokens

**Color** — base palette plus a separately-justified severity palette (severity colors are functional, not decorative — they must always mean the same thing everywhere):

| Token | Hex | Use |
|---|---|---|
| `--bg-base` | `#14181D` | App background — charcoal-blue, not pure black |
| `--bg-surface` | `#1C2229` | Panels, cards |
| `--border-hairline` | `#2A3038` | Dividers, card borders |
| `--text-primary` | `#E8EAED` | Primary text |
| `--text-secondary` | `#8B939E` | Secondary/meta text |
| `--accent-signal` | `#E8A33D` | Active states, selected module, focus rings — brand accent, used sparingly |

| Severity token | Hex | Meaning (must stay consistent everywhere) |
|---|---|---|
| `--sev-critical` | `#E24B4A` | Critical red flag, high risk score |
| `--sev-high` | `#BA7517` | High-severity flag |
| `--sev-verified` | `#4FA66B` | Legitimate / cleared |
| `--mod-network` | `#3FB6C7` | NetworkX module accent — "active trace" cyan |
| `--mod-enforce` | `#C99A3B` | CrimeMap module accent — "deploy" gold |

**Typography** — three roles, each doing a distinct job:
- **Display/headers:** a condensed grotesk (IBM Plex Sans Condensed, or Archivo Narrow as fallback) — gives headers a case-file masthead authority without leaning on a serif.
- **Body:** Inter or IBM Plex Sans — neutral, legible at small sizes for dense data tables and flag descriptions.
- **Data/mono:** IBM Plex Mono or JetBrains Mono — reserved for audit IDs, risk scores, timestamps, coordinates, and quoted evidence phrases. This face is what visually signals "this is real structured system output," reinforcing the auditability pitch every time it appears.

**Layout concept:**

```
┌──────────────────────────────────────────────────────────────────┐
│  KAVACH   [cases: 142]  [campaigns: 3]  [top priority: Pune]     │ ← status masthead
├───────────┬──────────────────────────────────────┬───────────────┤
│           │                                      │               │
│  Module   │                                      │   Dossier     │
│  Rail     │            Main Canvas               │   Panel       │
│           │   (FraudScope input / NetworkX       │  (active case │
│  01       │    graph / CrimeMap choropleth,       │   detail —    │
│  FraudScope│   depending on selected module)      │   persists    │
│  02       │                                      │   across      │
│  NetworkX │                                      │   modules)    │
│  03       │                                      │               │
│  CrimeMap │                                      │               │
└───────────┴──────────────────────────────────────┴───────────────┘
```

The module rail keeps the "01/02/03" numbering from the original pitch deck — that's justified here because it's a real fixed sequence in the product's own framing (detect → network → map), not decoration. The dossier panel on the right is what makes cross-module context visible at all times instead of forcing a re-search — this single piece of layout *is* requirement C.1 from `FEATURE_REQUIREMENTS.md`.

**Signature element — "Evidence Trace":** when a case is classified, the original pasted text is shown with matched red-flag phrases underlined inline in their severity color, each with a thin leader line to its corresponding flag card in the dossier panel — like annotated markup on a case file. This is the one deliberately memorable visual moment in the product, and it's earned by the content (it's literally showing the audit trail), not decoration for its own sake.

## Page / route map

| Route | Module | Primary content |
|---|---|---|
| `/` | — | Status overview: aggregate metrics, recent cases, top-priority district (P2, build last) |
| `/fraudscope` | FraudScope | Text input, result card, Evidence Trace |
| `/network` | NetworkX | Force graph, campaign cards, case detail on node click |
| `/crimemap` | CrimeMap | Choropleth, district tooltip, enforcement ranking list |

## Component inventory (maps directly to `PROJECT_STRUCTURE.md`)

- `StatusBar` — masthead, live counts
- `ModuleRail` — the 01/02/03 navigation
- `DossierPanel` — persistent active-case detail, shared across routes via `CaseContext`
- `ClassifierInput` — text area + submit, loading state shown as a state label change, not a spinner animation, to keep the "terminal" feel
- `ResultCard` — risk ring, verdict banner, flag list
- `EvidenceTrace` — the signature inline-annotation element
- `ForceGraph` — D3 force-directed graph wrapper, exposes `onNodeClick`, `addNode()`
- `CampaignCard` — cluster summary
- `Choropleth` — D3 geo wrapper
- `DistrictTooltip` — hover detail

## State management

`CaseContext` (React context) holds the currently active case/campaign/district. Set whenever a case is classified or selected anywhere in the app; read by all three module pages and the `DossierPanel`. Everything else is local component state — no global store needed at this scope.

## Accessibility & responsiveness notes

- Severity always paired with an icon or text label, never color alone (colorblind-safe by construction).
- Visible focus rings using `--accent-signal`, keyboard navigation across the module rail.
- The three-pane layout collapses to a single-column stack with a tab switcher below tablet width — the dossier panel becomes a slide-up sheet rather than disappearing, since persistent context matters on mobile too (a field officer is a realistic mobile user for this product).

## What "looks like an AI demo" to avoid explicitly

No centered single-column chat layout. No message bubbles. No animated "thinking" shimmer or typing dots. No rounded gradient hero card on the landing view. No stock circuit-board/robot iconography. No purple-to-blue gradient buttons (the most common generic-AI-app tell). Loading states should read as system states (`ANALYZING…`, `QUEUED`, `CLUSTERING`) in the mono data face, not spinner animations — this alone does a lot of work toward the "intelligence system, not chatbot" feel.

---

## Google Stitch prompt

Paste the following into Google Stitch as the initial generation prompt. Treat the Stitch output as a high-fidelity visual reference to hand-translate into the actual React/D3 components above — Stitch won't generate the D3 graph/map interactivity itself, but it's excellent for nailing the shell layout, color application, and typography feel before you write a line of component code.

```
Design a desktop web application called KAVACH — a cybercrime intelligence
console used by police analysts in India, not a consumer chatbot. The tone
is serious, calm, and information-dense, like a case-management or NOC
monitoring tool, not a friendly AI assistant product.

Layout: a three-pane shell. Top masthead bar showing the product name and
three live metrics (total cases, active campaigns, top-priority district).
Below it, a narrow left sidebar listing three numbered modules (01
FraudScope, 02 NetworkX, 03 CrimeMap) as vertical nav items. Center is the
main working canvas. Right is a persistent narrow "case dossier" panel
showing details of whichever case is currently active.

Color palette: charcoal-blue background (#14181D), slightly lighter panel
surfaces (#1C2229), hairline borders (#2A3038), off-white primary text
(#E8EAED), muted grey secondary text (#8B939E). A warm amber accent
(#E8A33D) used sparingly for active/selected states only. Do NOT use
purple-to-blue gradients, glowing neon effects, or bright saturated colors
as the dominant palette.

Typography: a condensed grotesk sans for headers and labels (feel: Archivo
Narrow / IBM Plex Sans Condensed), a clean neutral sans for body text
(feel: Inter), and a monospace face reserved specifically for IDs,
timestamps, scores, and quoted evidence text (feel: IBM Plex Mono /
JetBrains Mono) — the monospace usage should visually signal "structured
system data" wherever it appears.

Design screen 1 — FraudScope: a large text input area where a user pastes
a suspicious message or call transcript, a clear "Analyze" action, and a
result view below showing: a circular risk score indicator (color shifts
green/amber/red by score), a one-line verdict banner, and a vertical list
of "red flag" cards each with a colored severity dot, a short label, a
monospace-styled quoted evidence phrase, and a one-line explanation.

Design screen 2 — NetworkX: the same shell, with the center canvas showing
a node-and-edge network graph (represent it as circles connected by lines,
grouped into 3 visually distinct colored clusters), with a small floating
summary card per cluster showing case count and estimated financial loss.

Design screen 3 — CrimeMap: the same shell, with the center canvas showing
a map of India shaded by district using a sequential color scale from pale
yellow (low priority) to deep red (high priority), and a small ranked list
panel below or beside it showing the top 5 priority districts with their
scores.

Overall feel: restrained, dense, authoritative, built for someone doing
serious investigative work — not playful, not consumer-friendly, not
"AI startup." Minimal use of icons; rely on typography, color, and layout
structure to convey hierarchy and severity.
```

**Suggested follow-up refinement prompts once Stitch generates a first pass:**

```
Make the module sidebar feel more like a fixed case-file index — use the
numbers 01/02/03 prominently, condensed type, more vertical whitespace
between items.
```

```
On the FraudScope result screen, show the original pasted text with the
matched red-flag phrases underlined in their severity color, with a thin
line connecting each underlined phrase to its corresponding flag card —
like annotated case file evidence markup.
```

```
Reduce any gradient or glow effects across all screens — flatten surfaces
to solid colors with hairline borders only, this should feel closer to
enterprise monitoring software than a marketing site.
```
