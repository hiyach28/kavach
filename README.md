# KAVACH v2 — Fraud-Defense Platform

> ET AI Hackathon 2026 · Problem #6: AI for Digital Public Safety.
> Real-time citizen protection (Shield) + law-enforcement campaign intelligence (Terminal) + court-ready evidence.

**Status: Phase 0 — foundations.** See [`ROADMAP.md`](ROADMAP.md) and [`FEATURE_STATUS.md`](FEATURE_STATUS.md) (single source of truth for implemented vs pending).

## Quickstart
```bash
cp .env.example .env       # defaults are safe: LLM_MODE=mock, no API key needed
docker compose up -d --build
make smoke                 # end-to-end sanity check
```
API: http://localhost:8000/health · UI: http://localhost:3000

## Documentation
Everything is indexed in [`docs/INDEX.md`](docs/INDEX.md). Feature IDs (F10–F62) thread through
specs (`docs/04`), status (`FEATURE_STATUS.md`), metrics (`docs/05`), tests (`docs/06`) and the
demo plan (`docs/07`). Agents/developers: read [`CLAUDE.md`](CLAUDE.md) first.

## v1
The original hackathon prototype was assessed in [`docs/00_ASSESSMENT.md`](docs/00_ASSESSMENT.md);
its reference code lives in [`legacy/`](legacy/). History was reset on 2026-07-08.
