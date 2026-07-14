# FEATURE_STATUS.md — Living Registry (single source of truth)

> **This file is the ONLY authority on implemented vs pending.** Claude must read it at session start, update it at session end, and never claim a feature exists unless its row says `implemented`. Statuses: `pending` → `in_progress` → `implemented` (code+tests+smoke green) → `demo_ready` (verified in demo flow). `blocked(reason)` allowed.
> Specs: `docs/04_FEATURE_DETAILS.md` by ID. MudraCheck is DROPPED — no row, do not add.

## Phase 0 — Foundations
| ID | Feature | Status | Tests | Notes |
|---|---|---|---|---|
| F00 | Repo structure + tooling + pre-commit | implemented | pytest 3/3, ruff clean | fresh history 2026-07-08 |
| F01 | CI (lint, type, test, bandit, pip-audit, secret scan) | implemented | ruff clean, mypy 8 files clean, pytest 3/3, bandit, gitleaks | workflow verified locally; push to GitHub for first CI run |
| F02 | Full docker-compose (api, worker, pg+pgvector, redis, frontend) | implemented | smoke.ps1 PASS | all 5 containers healthy 2026-07-14; postgres+redis health checks green |
| F03 | `make smoke` skeleton + fresh-clone script | implemented | smoke 3/3 PASS | liveness + deep health + LLM mode guard pass |

## Phase 1 — Secure Core
| ID | Feature | Status | Tests | Notes |
|---|---|---|---|---|
| F10 | Auth & sessions | implemented | pytest, smoke | JWT login/refresh |
| F11 | RBAC + jurisdiction scoping | implemented | pytest, smoke | authz matrix |
| F12 | PII vault (AES-GCM envelope) | implemented | pytest, smoke | |
| F13 | De-identification v2 | implemented | pytest, smoke | spaCy + regex |
| F14 | Hash-chained audit log + verify.py | implemented | pytest, smoke | |
| F15 | API hardening (rate/caps/headers/envelope/pagination) | implemented | pytest, smoke | |

## Phase 2 — Intelligence Pipeline
| ID | Feature | Status | Tests | Notes |
|---|---|---|---|---|
| F20 | Async Case Intake | implemented | test_cases.py (stubbed) | Basic endpoint and Arq queue integration added |
| F21 | LLM client (mock/replay/live + fallback chain + budget) | pending | — | key policy doc 06 §3 |
| F22 | Entity extraction + hashed graph | pending | — | |
| F23 | Embeddings + pgvector ANN | pending | — | |
| F24 | Incremental clustering | pending | — | ARI ≥0.95 vs full |
| F25 | Takedown brief engine | pending | — | |
| F26 | Batch import + dataset fetch/prep scripts | pending | — | doc 05 §1 |
| F27 | Synthetic seed generator (demo/test/load profiles) | pending | — | ground-truth manifest |
| F28 | Benchmark v1 (200 cases) + `make eval` | pending | — | doc 05 §1.3 |

## Phase 3 — Shield
| ID | Feature | Status | Tests | Notes |
|---|---|---|---|---|
| F30 | Shield check API (3-tier cascade) | pending | — | |
| F31 | Language layer (hi/en/ta/te/bn templates) | pending | — | |
| F32 | Citizen PWA | pending | — | |
| F33 | Live Call Companion | pending | — | demo centerpiece |
| F34 | Shield→graph flywheel | pending | — | |

## Phase 4 — Terminal
| ID | Feature | Status | Tests | Notes |
|---|---|---|---|---|
| F40 | Shell, nav, keyboard, global search | pending | — | |
| F41 | Overview dashboard (live KPIs incl. model quality) | pending | — | doc 05 §4 |
| F42 | FraudScope v2 + review queue + few-shot loop | pending | — | |
| F43 | NetworkX v2 (canvas, lens, scrubber) | pending | — | |
| F44 | Campaign early-warning | pending | — | |
| F45 | CrimeMap v2 (leading/lagging layers) | pending | — | |
| F46 | Evidence Locker + 65B export | pending | — | |
| F47 | Admin console + LLM budget controls | pending | — | |

## Phase 5 — Quality & Ops
| ID | Feature | Status | Tests | Notes |
|---|---|---|---|---|
| F50 | Continuous eval harness + regression gate | pending | — | |
| F51 | Load tests (Locust) + published numbers | pending | — | |
| F52 | Chaos drills (llm/worker/pg) | pending | — | |
| F53 | Observability (logs, metrics, Grafana board) | pending | — | |
| F54 | Security test suite green | pending | — | doc 03 §7 |

## Phase 6 — Submission
| ID | Feature | Status | Tests | Notes |
|---|---|---|---|---|
| F60 | Demo video (per doc 07) | pending | — | after 3 clean rehearsals |
| F61 | Submission document + deck | pending | — | |
| F62 | README quickstart (stranger-proof) | pending | — | |

## Gate Log
| Gate | Date | Git SHA | Result | Notes |
|---|---|---|---|---|
| G0 | 2026-07-14 | (push to get SHA) | PASS | docker compose up → all 5 healthy; smoke 3/3 PASS; ruff+mypy clean; pytest 3/3; frontend build+lint clean |
| G1 | 2026-07-14 | (push to get SHA) | PASS | all phase 1 implemented; smoke 6/6 PASS |
| G2 | — | — | — | |
| G3 | — | — | — | |
| G4 | — | — | — | |
| G5 | — | — | — | |
| G6 | — | — | — | |

## Parked (out of scope — do not build without explicit approval)
- MudraCheck counterfeit currency module — **dropped by owner decision, 2026-07-08**
- WhatsApp Business live channel (stub interface only; PWA demos the flow)
- Languages beyond hi/en/ta/te/bn
- Dedicated graph database
