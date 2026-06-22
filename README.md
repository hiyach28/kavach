# KAVACH - Cybercrime Intelligence Platform

## 1. Project Overview

**KAVACH** is a next-generation cybercrime intelligence and investigation platform built for Indian law enforcement agencies. 

**The Problem**: Cybercrime in India (like "Digital Arrests", Investment Scams, and Courier Frauds) is exploding. Investigators are overwhelmed with unstructured complaint transcripts, SMS screenshots, and WhatsApp logs. Connecting these isolated incidents into organized criminal networks is currently a slow, manual process.

**The Solution**: KAVACH acts as an "Investigator's Terminal." It ingests raw evidence, redacts Personally Identifiable Information (PII) to protect victims, uses Large Language Models (LLMs) to automatically classify the fraud, extracts malicious infrastructure (phone numbers, UPI IDs), and algorithmically clusters these cases into organized fraud rings.

**Target Users**: Cybercrime analysts, nodal officers, and law enforcement task forces.

---

## 2. Core Modules

### FraudScope
**Purpose**: Automated evidence processing and classification.
* **User Workflow**: An investigator pastes a complaint transcript or uploads a screenshot (OCR).
* **Inputs**: Text, SMS, WhatsApp screenshots.
* **Outputs**: A structured fraud verdict, Risk Score (0-100), and an Evidence Trace.
* **Key Capabilities**: 
  * Local PII redaction (phones, Aadhaar, bank accounts) before LLM analysis.
  * LLM-driven Red Flag detection with citations to MHA/NCRB advisories.
  * Extracted malicious identifiers (Infrastructure nodes).

### NetworkX
**Purpose**: Intelligence graph visualization and fraud ring detection.
* **User Workflow**: Navigate to the graph after classification to see how the new case connects to existing ones.
* **Inputs**: Case-to-Infrastructure links and Semantic text embeddings.
* **Outputs**: A dynamic D3 force-directed graph grouping cases into "Campaigns."
* **Key Capabilities**:
  * Uses the Louvain community detection algorithm to cluster cases.
  * Highlights high-centrality infrastructure nodes (the "lynchpins" of a scam).

### CrimeMap
**Purpose**: Geospatial intelligence and resource allocation.
* **User Workflow**: View the choropleth map to see the hardest-hit districts.
* **Inputs**: Geographic data, complaint volumes, financial losses, and active campaign counts.
* **Outputs**: A priority-ranked list of districts.
* **Key Capabilities**:
  * Blends static NCRB data with dynamic LLM-classified case intelligence.
  * Drill-down into a specific district to view localized case logs.

---

## 3. Try KAVACH (Demo Testing)

If you want to test the platform immediately, start here:
(docs/TRY_KAVACH.md)

**Sample Investigation Datasets**:
* [Sample 1: Digital Arrest Scam](docs/sample-cases/sample-fraud-case-01.md)
* [Sample 2: Fake Investment Scam](docs/sample-cases/sample-fraud-case-02.md)
* [Sample 3: Courier / Customs Scam](docs/sample-cases/sample-fraud-case-03.md)

---

## 4. Platform Features

* **In-Browser OCR**: Upload images and extract text entirely client-side using `tesseract.js`.
* **Zero-Leakage PII Masking**: Victim phone numbers and Aadhaar IDs are regex-masked locally before any cloud LLM API calls.
* **Automated Graph Clustering**: Every new case immediately updates the Louvain clustering algorithm on the backend to detect new campaigns.
* **Cross-Module Context**: Selecting a case in FraudScope instantly centers it in the NetworkX graph and updates the global Dossier panel.

---

## 5. Architecture & Tech Stack

### High-Level Flow
`UI (React)` -> `OCR/Masking` -> `FastAPI Backend` -> `Gemini LLM` -> `SQLite DB` -> `Louvain Clustering` -> `UI Updates`

### Tech Stack
* **Frontend**: React 19, Vite, D3.js (Graph Visualization), Vanilla CSS (Custom Design System).
* **Backend**: Python 3, FastAPI, SQLAlchemy.
* **Database**: SQLite (`kavach.db`).
* **AI/ML**: Google GenAI SDK (`gemini-2.5-flash`), NetworkX, `python-louvain`.

---

## 6. Folder Structure

```text
kavach/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI entry point
│   │   ├── models.py               # SQLAlchemy DB models
│   │   ├── schemas.py              # Pydantic validation
│   │   ├── routes/                 # API Endpoints (FraudScope, NetworkX, CrimeMap)
│   │   └── services/               # Core Logic (Clustering, LLM client)
│   ├── seed/                       # Mock data generation scripts
│   └── requirements.txt            # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx                 # Main Application Layout & Router
│   │   ├── context/CaseContext.jsx # Global State Management
│   │   ├── components/             # React Components (Shell, FraudScope, NetworkX)
│   │   ├── pages/                  # Top-level Views
│   │   └── index.css               # Design System and Utility Classes
│   ├── package.json
│   └── vite.config.js
├── docs/                           # Architecture and Sample Cases
├── .env                            # Environment Configuration
└── docker-compose.yml              # Containerization
```

---

## 7. Installation & Setup

**Prerequisites**:
* Docker and Docker Compose (Recommended)
* A Google Gemini API Key

**1. Clone the repository**:
```bash
git clone https://github.com/hiyach28/kavach.git
cd kavach
```

**2. Environment Setup**:
Copy the example environment file and add your Gemini API Key.
```bash
cp .env.example .env
# Edit .env to include: GEMINI_API_KEY="your_api_key_here"
```

---

## 8. Running Locally

The easiest and recommended way to run KAVACH is via Docker Compose. This ensures the frontend and backend run in synchronized environments.

**Option A: Docker Compose (Recommended)**
```bash
docker-compose up --build
```
Access the application at: **http://localhost:3000**
*(The backend API will be available at `http://localhost:8000`)*

**Option B: Alternatively (Bare-Metal)**

If you prefer not to use Docker, you can run the services manually. You will need Node.js (v18+) and Python 3.10+.

*Terminal 1 (Backend)*:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Or `.venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

*Terminal 2 (Frontend)*:
```bash
cd frontend
npm install
npm run dev
```
Access the application at: **http://localhost:3000**

---

## 9. Seed Data

To demonstrate the graph and map modules out-of-the-box, KAVACH includes a robust mock data seeder.
The seed data includes 36 pre-classified cases, 10 geographic districts, and 5 active fraud rings (campaigns).

To reset or regenerate the database:
```bash
cd backend
rm kavach.db
python -m seed.seed_cases
python -m seed.seed_districts
```

---

## 10. API Documentation

When the backend is running, FastAPI auto-generates comprehensive OpenAPI documentation.
* **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

**Key Endpoints**:
* `POST /api/classify`: Takes raw text, returns LLM verdict and red flags.
* `GET /api/graph`: Returns nodes, links, and campaign data for D3.
* `GET /api/districts`: Returns priority-ranked geographic statistics.

---

## 11. Testing

* **Frontend Build Check**: `npm run build` (Ensures Vite bundles correctly).
* **Backend Unit Tests**: (If implemented) `pytest tests/`.
* **Manual UI Testing**: Follow the guide in `docs/TRY_KAVACH.md`.

---

## 12. Troubleshooting

**1. API Classification Fails (Status: PENDING)**
* **Cause**: Invalid or missing `GEMINI_API_KEY` in `.env`, or the LLM returned invalid JSON.
* **Fix**: Verify your API key. The system is designed to degrade gracefully to a `needs_manual_review` state rather than crashing.

**2. D3 Graph Not Showing Links**
* **Cause**: You may be testing with a completely unique case that shares no infrastructure (phone numbers) with existing database items.
* **Fix**: Ensure your test cases share at least one 10-digit number (e.g., `9876543210`) to see link generation.

**3. Frontend React crashes**
* **Cause**: Usually missing Node packages. 
* **Fix**: Run `npm install` inside the `frontend` directory.

---

## 13. Future Roadmap

1. **Multilingual Support**: Implement Bhashini API integration for translation of regional Indian languages before LLM analysis.
2. **WebSockets**: Real-time graph updates when other investigators classify connected cases.
3. **Advanced RAG**: Connect the LLM to a vector database of historic FIRs to improve `mha_ncrb_citation` accuracy.
