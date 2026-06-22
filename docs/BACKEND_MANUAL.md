# KAVACH Backend Manual & Architecture Flow

This document outlines the final, production-ready backend architecture for the KAVACH MVP. It serves as a comprehensive guide for the system's infrastructure, its heavily mocked dataset, the precise flow of data across our intelligence modules, and the strategic importance of this architecture.

## 1. System Architecture

The KAVACH backend is an orchestrated microservices-style monolith built with:
- **FastAPI**: Core async framework for high-throughput routing.
- **SQLite (SQLAlchemy ORM)**: Local relational data store acting as the source of truth for cases, infra nodes, and district analytics.
- **Pydantic v2**: Rigid data validation and strict API contract enforcement.
- **Google Gemini API**: Advanced LLM used strictly as a reasoning engine, bound by structured JSON outputs.

The backend is structurally divided into three cohesive intelligence layers that communicate via the central database.

### The Intelligence Layers
1. **FraudScope (Classification)**: `POST /api/classify`
2. **NetworkX (Clustering)**: `GET /api/graph`
3. **CrimeMap (Geospatial Priority)**: `GET /api/districts`

---

## 2. The User Flow (Data Pipeline)

The backend is not just a collection of endpoints; it is an active data pipeline. Here is the exact lifecycle of a piece of intelligence moving through the KAVACH system:

### Step 1: Ingestion & De-Identification
1. A user (or portal) submits a raw text complaint via `POST /api/classify`.
2. The `deidentify.py` service scans the text using regex. It extracts sensitive PII (Phone numbers, Bank Accounts, Emails, URLs, Crypto Wallets).
3. The PII is replaced with tokens (e.g., `[PHONE_1]`), and the mapping is securely stored in a separate table (`pii_token_map`).

### Step 2: LLM Reasoning (FraudScope)
1. The sanitized, PII-free text is sent to the Gemini 2.5 Flash model via `llm_client.py`.
2. The model is forced to output a strictly structured JSON response (`LLMFraudVerdict`) detailing the fraud category, risk score, confidence, and specific red flags.
3. *Resilience*: If the LLM hallucinates an invalid JSON string, the backend automatically intercepts the error and fires a retry prompt with explicit formatting constraints. If it fails again, it degrades gracefully to a `needs_manual_review` state rather than crashing.

### Step 3: Graph Projection & Clustering (NetworkX)
1. Once classified, the case is saved to SQLite.
2. Crucially, the backend maps the extracted PII tokens into **InfraNodes** (e.g., a node for `+919876543210`).
3. The system fires `recluster_campaigns()`. It builds an undirected graph of Cases connected via shared InfraNodes using the Louvain community detection algorithm.
4. The system discovers "Campaigns" (clusters of related cases) and updates the database.

### Step 4: Prioritization (CrimeMap)
1. Cases inherently belong to a `district`.
2. `priority_scoring.py` actively calculates a live threat score for every district in India using the formula:
   `Priority Score = (Volume * 0.4) + (Growth Rate * 0.35) + (Financial Impact * 0.25)`
3. A frontend user pulling `GET /api/districts/Jamtara/summary` will dynamically receive the aggregate district stats *and* the cross-referenced number of active campaigns discovered in Step 3.

---

## 3. The Seeded Environment (Mock Data)

To simulate a live, highly active intelligence environment, the backend is pre-seeded with **36 sophisticated cases clustered into 5 distinct criminal campaigns** across **10 major Indian districts**.

### The 5 Active Campaigns:
1. **Digital Arrest Ring** (Mumbai): 5 cases sharing a single HDFC Bank Account.
2. **Investment/Crypto Scam** (Delhi): 6 cases linked by a common Telegram Admin Phone Number.
3. **OTP/SIM Swap Ring** (Jamtara): 7 cases anchored to a fake Paytm KYC support email.
4. **Courier/Parcel Scam** (Bangalore): 10 high-volume cases linked by a common device fingerprint footprint.
5. **Job Fraud** (Pune): 8 cases orchestrated through a single WhatsApp number.

This rich dataset guarantees that the D3.js Force Graph and the Choropleth maps in the UI will have dense, interconnected data to visualize immediately upon launch.

---

## 4. Strategic Importance

Why did we build it this way?

1. **Zero-Trust AI**: By enforcing Pydantic validation on the LLM output and aggressively de-identifying data before it hits the cloud, KAVACH proves that government-grade privacy is possible while leveraging cutting-edge LLMs.
2. **Deterministic Fallbacks**: Hackathons fail when APIs go down or models hallucinate. Our backend guarantees safety by wrapping the LLM in try/catch loops and defaulting to manual review.
3. **Cross-Module Cohesion**: KAVACH is not 3 separate apps. It is 1 app. A case entered in FraudScope dynamically alters the physical shape of the NetworkX graph and instantly recalculates the resource allocation priority in CrimeMap. 

The backend is completely documented, fully tested via `pytest`, comprehensively seeded, and 100% compliant with the `integration-checklist.md` contracts.

**Status:** Ready for Frontend Integration.
