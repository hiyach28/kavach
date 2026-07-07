#!/usr/bin/env bash
# KAVACH smoke suite — grows one assertion per feature (docs/06 §1.2).
# Phase 0 scope: services boot, health endpoints green, worker responds.
set -euo pipefail
BASE="${BASE:-http://localhost:8000}"

echo "[smoke] 1/3 liveness"
curl -sf "$BASE/health" | grep -q '"status":"ok"'

echo "[smoke] 2/3 readiness (postgres+redis)"
curl -sf "$BASE/health/deep" | grep -q '"status":"ok"' || { echo "FAIL: deep health degraded"; exit 1; }

echo "[smoke] 3/3 llm mode guard (must not be live outside demo)"
curl -sf "$BASE/health" | grep -qE '"llm_mode":"(mock|replay)"' || { echo "FAIL: LLM_MODE=live outside demo!"; exit 1; }

echo "[smoke] PASS"
