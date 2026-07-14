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

echo "[smoke] 4/6 auth/login (wrong creds) -> 401"
RESP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/v1/auth/login" -H "Content-Type: application/json" -d '{"email":"fake@fake.com","password":"fake"}')
[ "$RESP" -eq 401 ] || { echo "FAIL: Expected 401 for bad login, got $RESP"; exit 1; }

echo "[smoke] 5/6 pii/decrypt (unauthed) -> 401"
RESP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/v1/pii/decrypt" -H "Content-Type: application/json" -d '{"token":"foo","justification":"bar"}')
[ "$RESP" -eq 401 ] || { echo "FAIL: Expected 401 for unauthed decrypt, got $RESP"; exit 1; }

echo "[smoke] 6/6 make sure error envelope is used"
curl -s -X POST "$BASE/v1/pii/decrypt" -H "Content-Type: application/json" -d '{"token":"foo","justification":"bar"}' | grep -q '"success":false' || { echo "FAIL: Missing error envelope"; exit 1; }

echo "[smoke] PASS"
