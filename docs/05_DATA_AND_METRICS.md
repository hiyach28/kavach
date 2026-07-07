# KAVACH v2 — Data, Datasets & Real-Time Metrics

Answers three questions with zero ambiguity: **what data do we train/eval/demo on**, **how is every stat computed**, and **where does each stat appear (app + demo video)**.

---

## 1. Datasets

### 1.1 Real public datasets (verified to exist — download in Phase 2, F26)

| Dataset | Source | Use in KAVACH |
|---|---|---|
| Fraud Call (India) Dataset | [Kaggle: narayanyadav/fraud-call-india-dataset](https://www.kaggle.com/datasets/narayanyadav/fraud-call-india-dataset) | Labeled fraud/normal call text — core eval set for classification |
| Scam / Non-Scam Call Conversations | [Kaggle: teeconnie](https://www.kaggle.com/datasets/teeconnie/scam-and-non-scam-call-conversation-dataset) | 400 conversation transcripts — Live Call Companion stage-detection fixtures |
| Comprehensive Indian Online Fraud Dataset | [Kaggle: kumarperiya](https://www.kaggle.com/datasets/kumarperiya/comprehensive-indian-online-fraud-dataset) | Transaction-style records w/ fraud categories, Indian cities — CrimeMap + campaign seeding |
| UCI SMS Spam Collection (5,574 msgs) | UCI ML Repository | Negative-class breadth; FP-rate testing on benign messages |
| Phishing Email Dataset | [Kaggle: naserabdullahalam](https://www.kaggle.com/datasets/naserabdullahalam/phishing-email-dataset) | Cross-channel red-flag patterns |
| NCRB "Crime in India" state/district cyber tables | ncrb.gov.in published tables | Real district-level complaint counts for CrimeMap static layer (replaces v1's invented weekly stats) |

Rules: check each license before bundling — if redistribution is unclear, ship a `scripts/fetch_datasets.py` downloader instead of committing data. Store under `data/external/`, never modified in place; all transforms go through `scripts/prepare_data.py` (reproducible).

### 1.2 Mock database — `scripts/seed_synthetic.py` (Phase 2, deterministic, seeded RNG)
Public datasets won't cover campaign structure, so generate it:
- **Scenario-based generation:** 12 scam script templates (digital arrest, UPI spoof, courier, investment, job, loan, OTP, KYC, electricity, lottery, sextortion, fake-police) × 5 languages × paraphrase variations (pre-generated ONCE with a live LLM run, cached to `data/synthetic/paraphrases.json`, committed — never regenerated in tests; see doc 06 §3).
- **Campaign structure:** N synthetic rings, each with a pool of entities (mule UPIs, phones) reused across cases with churn (entities "burn" over time — tests semantic linking), geographic spread, and a timestamp process (Poisson base + burst injection for early-warning testing).
- **Ground truth manifest:** every synthetic case carries hidden labels (`true_campaign_id`, `true_fraud_type`, `true_entities`) in a side table → this is what accuracy metrics are computed against.
- Sizes: `--profile demo` (500 cases, 8 campaigns), `--profile test` (5k), `--profile load` (100k).

### 1.3 Labeled eval benchmark — `data/benchmark/` (Phase 2→5, versioned)
- 200 cases: 120 from real Kaggle sets (relabeled to our fraud-type enum), 50 synthetic hard cases, 30 **benign** (job offers, real bank SMS, courier updates — FP-rate guards, the "must be very low" eval criterion).
- Format: JSONL `{id, text, language, true_type, true_entities[], source}`. Frozen per version (`benchmark-v1`); corrections from the review queue (F42) accumulate into `benchmark-v2` — never edit a frozen version.

## 2. Model Accuracy — exact definitions (no hand-waving in front of judges)

| Metric | Definition | Computed |
|---|---|---|
| Classification precision/recall/F1 | Per fraud-type vs benchmark truth, macro-averaged | F50 harness, every CI run in `replay` mode + nightly |
| **False-positive rate** | benign cases classified as any fraud / total benign | Same; **target <2%**, alert if above |
| Entity extraction F1 | Exact-match hashes vs `true_entities` | Same |
| Campaign accuracy (ARI) | Adjusted Rand Index of predicted vs `true_campaign_id` on synthetic set | After clustering runs on test profile |
| Early-warning lead time | (first-alert time) − (first case of injected burst) on replay fixtures | F44 tests |
| Shield latency p50/p95 | From `shield_checks.latency_ms` | Live, continuously |
| Degraded-mode delta | Accuracy of RulesOnlyClassifier vs LLM on benchmark | Once per benchmark version (honesty metric) |

**Continuous eval (F50):** `make eval` runs benchmark → writes a row to `eval_runs` (model, mode, per-metric scores, git SHA) → dashboard reads latest. CI fails if F1 drops >3 points vs last accepted run (regression gate).

## 3. Learning loop
Analyst corrections in the review queue → `case_feedback` → (a) appended to next benchmark version, (b) top-k similar corrected cases injected as few-shot examples into the classification prompt (few-shot store, capped 8 examples, selected by ANN). Measurable claim for demo: "the system's accuracy improves with every analyst correction — here's the eval graph across versions."

## 4. Real-time stats — where each number lives in the UI

| Stat | UI location | Update mechanism |
|---|---|---|
| Precision / recall / FP-rate (latest eval) | Overview KPI card "Model Quality" + Admin → Evaluation tab (trend chart across eval_runs) | On eval completion (SSE) |
| Shield checks 24h, p95 latency, tier-resolution split | Overview KPI + Shield ops panel | SSE, 5s aggregate |
| Cases by status (queued/classifying/…) | Overview pipeline widget | SSE per transition |
| Active campaigns, velocity sparklines | Overview + NetworkX campaign drawer | `campaign.updated` events |
| Early-warning alerts + projected victims | Amber banner + Overview | Cron → SSE |
| LLM cost today / budget remaining | Admin + small Overview badge | Per-call metering |
| Every KPI card has an ⓘ tooltip stating formula + data source verbatim from §2. | | |

## 5. Showing stats in the demo video (cross-ref `07_DEMO_PLAYBOOK.md`)
- **Never say a number without showing its source.** Each claimed metric gets a 2–3s zoom on its KPI card or the eval trend chart.
- Live beats: Shield latency shown by the on-screen stopwatch overlay (screen recorder timestamp), not a claim.
- Accuracy: cut to Admin → Evaluation tab: benchmark table (precision/recall/FP per class) + trend line across eval runs ("v1 prompt → v2 few-shot: +9 F1").
- Early warning: replay fixture triggers on camera; lead-time metric appears in the alert itself ("first alert 41 min after burst start, 2 cases in").
- Scale: 5s cut of Grafana during the Locust run (p95 lines + 100 req/s counter).
