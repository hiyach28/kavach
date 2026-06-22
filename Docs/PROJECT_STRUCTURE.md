# PROJECT_STRUCTURE.md — KAVACH

Monorepo layout — backend and frontend live side by side so the cross-module chain (the product's core feature) is easy to develop and test together.

```
kavach/
├── AGENTS.md
├── GUIDELINES.md
├── FEATURE_REQUIREMENTS.md
├── DATABASE_SCHEMA.md
├── ARCHITECTURE.md
├── FRONTEND_PLAN.md
├── docker-compose.yml
├── .env.example
│
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app instantiation, CORS, router includes
│   │   ├── config.py                # env var loading
│   │   ├── database.py              # SQLAlchemy engine/session setup
│   │   ├── models.py                # SQLAlchemy ORM models (mirrors DATABASE_SCHEMA.md)
│   │   ├── schemas.py               # Pydantic request/response models
│   │   ├── deidentify.py            # PII masking logic — used by every Claude call, no exceptions
│   │   ├── claude_client.py          # wraps Anthropic API calls, retry logic, audit logging
│   │   ├── routes/
│   │   │   ├── fraudscope.py        # POST /classify, GET /cases/{id}
│   │   │   ├── networkx_routes.py   # GET /graph, POST /graph/recluster
│   │   │   ├── crimemap.py          # GET /districts, GET /districts/{name}/summary
│   │   │   └── audit.py             # GET /audit/{audit_id}
│   │   ├── services/
│   │   │   ├── clustering.py        # Louvain clustering, campaign assignment
│   │   │   └── priority_scoring.py  # CrimeMap priority formula
│   │   └── tests/
│   │       ├── test_fraudscope.py
│   │       ├── test_clustering.py
│   │       └── test_priority_scoring.py
│   ├── seed/
│   │   ├── seed_cases.py            # generates the 15-20 mock cases / 3 campaigns
│   │   └── seed_districts.py        # loads NCRB-pattern district mock stats
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── client.js            # single fetch wrapper, all API calls go through here
│   │   ├── context/
│   │   │   └── CaseContext.jsx      # cross-module active-case state (Requirement C.1)
│   │   ├── components/
│   │   │   ├── shell/
│   │   │   │   ├── StatusBar.jsx
│   │   │   │   ├── ModuleRail.jsx
│   │   │   │   └── DossierPanel.jsx
│   │   │   ├── fraudscope/
│   │   │   │   ├── ClassifierInput.jsx
│   │   │   │   ├── ResultCard.jsx
│   │   │   │   └── EvidenceTrace.jsx   # the inline-underline signature element
│   │   │   ├── networkx/
│   │   │   │   ├── ForceGraph.jsx
│   │   │   │   └── CampaignCard.jsx
│   │   │   └── crimemap/
│   │   │       ├── Choropleth.jsx
│   │   │       └── DistrictTooltip.jsx
│   │   ├── pages/
│   │   │   ├── FraudScopePage.jsx
│   │   │   ├── NetworkXPage.jsx
│   │   │   └── CrimeMapPage.jsx
│   │   ├── styles/
│   │   │   └── tokens.css           # design tokens from FRONTEND_PLAN.md as CSS variables
│   │   └── App.jsx
│   ├── public/
│   │   └── india-districts.geojson
│   ├── package.json
│   └── Dockerfile
│
└── data/
    └── mock/
        ├── cases_seed.json
        └── districts_seed.json
```

## Rationale for the non-obvious choices

- **`deidentify.py` is its own module**, not a helper buried in the route file — it's a hard rule (`AGENTS.md`) that no Claude call skips it, so it needs to be the kind of file that's impossible to miss in review.
- **`services/` is separate from `routes/`** — clustering and scoring logic should be testable and callable independently of the HTTP layer (e.g. from a scheduled job later), not coupled to a request/response cycle.
- **`context/CaseContext.jsx` exists as its own folder**, not a generic "state" dumping ground — it exists specifically to satisfy the cross-module persistence requirement, and should stay scoped to that.
- **`EvidenceTrace.jsx` is named explicitly**, not folded into `ResultCard.jsx` — it's the design system's signature element (see `FRONTEND_PLAN.md`) and deserves to be independently reusable and testable.
