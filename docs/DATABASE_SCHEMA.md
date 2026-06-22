# DATABASE_SCHEMA.md — KAVACH

Dev DB: SQLite. Production path: Postgres (same schema, swap the SQLAlchemy connection string — avoid SQLite-specific types so this migration stays a one-line change).

## Entity overview

```
Case ──< CaseRedFlag
Case ──< CaseInfraLink >── InfraNode
Case ──< CaseFeedback
Case }── District (by district name, denormalized for query speed)
Campaign ──< Case (campaign_id assigned after clustering, nullable until clustered)
District ──< DistrictWeeklyStat
AuditLog (append-only, references Case by audit_id)
```

## Tables

### `cases`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| audit_id | TEXT UNIQUE NOT NULL | UUID, returned to client, the legal-traceability key |
| raw_text_deidentified | TEXT NOT NULL | Text after PII masking — never store the original raw text in this table |
| pii_token_map | TEXT | JSON, maps `[PHONE_1]` etc. back to real values, stored separately from the case text for access control |
| fraud_type | TEXT | enum: digital_arrest, upi_spoofing, otp_sim_swap, investment_fraud, job_loan_scam, courier_parcel, legitimate, needs_manual_review |
| risk_score | INTEGER | 0-100, nullable if needs_manual_review |
| confidence | REAL | 0.0-1.0 |
| verdict | TEXT | plain-language one-liner |
| reporting_portal | TEXT | URL |
| district | TEXT | nullable, self-reported or inferred |
| campaign_id | INTEGER FK → campaigns.id | nullable until clustering runs |
| status | TEXT | classified \| needs_manual_review \| confirmed \| false_positive |
| created_at | TIMESTAMP | UTC |

### `case_red_flags`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| case_id | INTEGER FK → cases.id | |
| flag_id | TEXT | e.g. `AUTH_IMP_001` |
| category | TEXT | critical \| high \| medium |
| evidence | TEXT | exact phrase from de-identified input |
| explanation | TEXT | why this is a red flag |

### `infra_nodes`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| type | TEXT | phone_pattern \| upi_handle \| bank_fragment \| device_id |
| value_hash | TEXT UNIQUE | hashed, never store the raw infra value in plaintext at rest |

### `case_infra_links`
| Column | Type | Notes |
|---|---|---|
| case_id | INTEGER FK → cases.id | |
| infra_node_id | INTEGER FK → infra_nodes.id | |
| (case_id, infra_node_id) | COMPOSITE PK | |

### `campaigns`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| label | TEXT | human-readable, e.g. "Campaign A — Mumbai mule ring" |
| case_count | INTEGER | denormalized, updated on re-clustering |
| total_estimated_loss | INTEGER | paise, denormalized |
| cross_jurisdiction | BOOLEAN | true if cases span >1 district — escalation flag |
| primary_target_infra_id | INTEGER FK → infra_nodes.id | the top-ranked takedown target by betweenness centrality |
| primary_target_betweenness | REAL | centrality score backing the recommendation |
| pct_connectivity_lost | REAL | collapse-impact: % of case-to-case links lost if primary_target is removed |
| fractures_network | BOOLEAN | true if removing primary_target splits the ring into more sub-components |
| last_clustered_at | TIMESTAMP | |

### `districts`
| Column | Type | Notes |
|---|---|---|
| name | TEXT PK | |
| state | TEXT | |
| geojson_id | TEXT | join key to the India districts GeoJSON properties |

### `district_weekly_stats`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| district_name | TEXT FK → districts.name | |
| week_start | DATE | |
| complaint_count | INTEGER | |
| estimated_loss | INTEGER | paise |
| priority_score | REAL | computed, 0-100 |

### `case_feedback` (P2 — human-in-the-loop)
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| case_id | INTEGER FK → cases.id | |
| marked_by | TEXT | officer identifier, nullable for hackathon scope |
| verdict | TEXT | confirmed \| false_positive |
| created_at | TIMESTAMP | |

### `audit_log` (append-only — never UPDATE or DELETE rows here)
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| audit_id | TEXT | matches cases.audit_id |
| event | TEXT | classify_attempt \| classify_success \| classify_failure \| reclassify |
| request_payload | TEXT | JSON, de-identified text only |
| response_payload | TEXT | JSON, raw Claude response before validation |
| latency_ms | INTEGER | |
| created_at | TIMESTAMP | |

## SQL (SQLite-compatible, Postgres-portable)

```sql
CREATE TABLE cases (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  audit_id TEXT UNIQUE NOT NULL,
  raw_text_deidentified TEXT NOT NULL,
  pii_token_map TEXT,
  fraud_type TEXT,
  risk_score INTEGER,
  confidence REAL,
  verdict TEXT,
  reporting_portal TEXT,
  district TEXT,
  campaign_id INTEGER REFERENCES campaigns(id),
  status TEXT NOT NULL DEFAULT 'classified',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE case_red_flags (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  case_id INTEGER NOT NULL REFERENCES cases(id),
  flag_id TEXT NOT NULL,
  category TEXT NOT NULL,
  evidence TEXT NOT NULL,
  explanation TEXT NOT NULL
);

CREATE TABLE infra_nodes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  type TEXT NOT NULL,
  value_hash TEXT UNIQUE NOT NULL
);

CREATE TABLE case_infra_links (
  case_id INTEGER NOT NULL REFERENCES cases(id),
  infra_node_id INTEGER NOT NULL REFERENCES infra_nodes(id),
  PRIMARY KEY (case_id, infra_node_id)
);

CREATE TABLE campaigns (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  label TEXT,
  case_count INTEGER DEFAULT 0,
  total_estimated_loss INTEGER DEFAULT 0,
  last_clustered_at TIMESTAMP
);

CREATE TABLE districts (
  name TEXT PRIMARY KEY,
  state TEXT,
  geojson_id TEXT
);

CREATE TABLE district_weekly_stats (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  district_name TEXT NOT NULL REFERENCES districts(name),
  week_start DATE NOT NULL,
  complaint_count INTEGER NOT NULL,
  estimated_loss INTEGER NOT NULL,
  priority_score REAL
);

CREATE TABLE case_feedback (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  case_id INTEGER NOT NULL REFERENCES cases(id),
  marked_by TEXT,
  verdict TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  audit_id TEXT NOT NULL,
  event TEXT NOT NULL,
  request_payload TEXT,
  response_payload TEXT,
  latency_ms INTEGER,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cases_campaign ON cases(campaign_id);
CREATE INDEX idx_cases_district ON cases(district);
CREATE INDEX idx_redflags_case ON case_red_flags(case_id);
CREATE INDEX idx_infralinks_infra ON case_infra_links(infra_node_id);
CREATE INDEX idx_weeklystats_district ON district_weekly_stats(district_name);
```

## Notes on scaling this schema later

- `pii_token_map` should move to a separate access-controlled table (or encrypted column) the moment this goes beyond a hackathon — it currently sits next to the case row for simplicity only.
- `audit_log` should become genuinely append-only at the database permission level (a role with INSERT-only grants) once this isn't just a demo — the schema already supports it, the enforcement is a deployment-time decision.
- When migrating to Postgres, add a `pgvector` column to `cases` for the script-similarity embedding (P2 feature in `FEATURE_REQUIREMENTS.md` 2.6) rather than bolting on a separate vector store.