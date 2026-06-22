# Backend Build Context & Phases

This document tracks the phased execution of the Kavach Backend build.

## Phase 1: Database & Schemas ✅
- **Status:** Completed
- **Components:** `models.py`, `schemas.py`, `database.py`, `config.py`.
- **Outcome:** SQLAlchemy ORM models mapped to strict Pydantic validation schemas.

## Phase 2: Core Services (Data Processing) ✅
- **Status:** Completed
- **Components:** `deidentify.py`, `llm_client.py`.
- **Goal:** Regex-based PII masking and Gemini API structured output integration.

## Phase 3: Core Services (Algorithms) ✅
- **Status:** Completed
- **Components:** `clustering.py`, `priority_scoring.py`.
- **Goal:** NetworkX graph clustering and CrimeMap weighted priority logic.

## Phase 4: API Routes ✅
- **Status:** Completed
- **Components:** `fraudscope.py`, `networkx_routes.py`, `crimemap.py`.
- **Goal:** Exposing the FastAPI endpoints according to `api-contracts.md`.

## Phase 5: Seeders & Integration ✅
- **Status:** Completed
- **Components:** `seed_cases.py`, `seed_districts.py`, `main.py` routing.
- **Goal:** Mock data injection and final wiring.
