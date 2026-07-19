.PHONY: up down test lint smoke seed-demo eval migrate import

up:
	docker compose up -d

down:
	docker compose down

migrate:
	docker compose run --rm migrator

test:
	cd backend && python -m pytest

lint:
	cd backend && ruff check . && mypy app

smoke:  ## end-to-end sanity — grows every phase (docs/06 §1)
	bash scripts/smoke.sh

seed-demo:  ## Phase 2 (F27): seed demo dataset (50 cases, 4 campaigns)
	cd backend && python scripts/seed_synthetic.py --profile demo

seed-test:  ## Phase 2 (F27): seed test dataset (200 cases, 11 campaigns)
	cd backend && python scripts/seed_synthetic.py --profile test

seed-load:  ## Phase 2 (F27): seed load-test dataset (5000+ cases, 30 campaigns)
	cd backend && python scripts/seed_synthetic.py --profile load --count 5000

eval:  ## Phase 2 (F28): run benchmark, writes eval_runs row
	cd backend && python -m eval.benchmark

eval-verbose:  ## Phase 2 (F28): run benchmark with per-case details
	cd backend && python -m eval.benchmark --verbose

import-csv:  ## Phase 2 (F26): batch import cases from CSV
	cd backend && python scripts/batch_import.py $(FILE) --format csv

import-json:  ## Phase 2 (F26): batch import cases from JSON
	cd backend && python scripts/batch_import.py $(FILE) --format json

fetch-datasets:  ## Phase 2 (F26): download external datasets
	bash backend/scripts/fetch_datasets.sh
