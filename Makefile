.PHONY: up down test lint smoke seed-demo eval

up:
	docker compose up -d --build

down:
	docker compose down

test:
	cd backend && python -m pytest

lint:
	cd backend && ruff check . && mypy app

smoke:  ## end-to-end sanity — grows every phase (docs/06 §1)
	bash scripts/smoke.sh

seed-demo:  ## Phase 2 (F27): restores exact demo dataset
	@echo "seed-demo: available from Phase 2 (F27)"

eval:  ## Phase 2 (F28): runs benchmark, writes eval_runs row
	@echo "eval: available from Phase 2 (F28)"
