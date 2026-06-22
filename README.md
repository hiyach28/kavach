# KAVACH - Fraud Intelligence Platform

KAVACH is a three-module fraud-intelligence platform designed to classify, cluster, and aggregate suspicious activities:
- **FraudScope**: Classifies suspicious text into a structured fraud verdict.
- **NetworkX**: Clusters classified cases into fraud-ring graphs.
- **CrimeMap**: Aggregates cases geospatially into an enforcement-priority ranking.

## Project Structure
The project is a monorepo containing both the FastAPI backend and React frontend.

For detailed architecture, schema, guidelines, and feature requirements, please refer to the documentation files.

## Running Locally

```bash
docker-compose up --build
# Backend: http://localhost:8000 (docs at /docs)
# Frontend: http://localhost:3000
```

Environment variables needed (see `.env.example`): `ANTHROPIC_API_KEY`, `DATABASE_URL`, `CORS_ORIGINS`.

## Documentation

- `ARCHITECTURE.md`
- `AGENTS.md`
- `DATABASE_SCHEMA.md`
- `FEATURE_REQUIREMENTS.md`
- `FRONTEND_PLAN.md`
- `GUIDELINES.md`
- `PROJECT_STRUCTURE.md`
