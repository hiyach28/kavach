#!/usr/bin/env bash
# KAVACH smoke suite — grows one assertion per feature (docs/06 §1.2).
# Phase 2 scope: Phase 0 + Phase 1 + campaign brief + admin stats.
set -euo pipefail
BASE="${BASE:-http://localhost:8000}"

echo "[smoke] 1/9 liveness"
curl -sf "$BASE/health" | grep -q '"status":"ok"'

echo "[smoke] 2/9 readiness (postgres+redis)"
curl -sf "$BASE/health/deep" | grep -q '"status":"ok"' || { echo "FAIL: deep health degraded"; exit 1; }

echo "[smoke] 3/9 llm mode guard (must not be live outside demo)"
curl -sf "$BASE/health" | grep -qE '"llm_mode":"(mock|replay)"' || { echo "FAIL: LLM_MODE=live outside demo!"; exit 1; }

echo "[smoke] 4/9 auth/login (wrong creds) -> 401"
RESP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/v1/auth/login" -H "Content-Type: application/json" -d '{"email":"fake@fake.com","password":"fake"}')
[ "$RESP" -eq 401 ] || { echo "FAIL: Expected 401 for bad login, got $RESP"; exit 1; }

echo "[smoke] 5/9 pii/decrypt (unauthed) -> 401"
RESP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/v1/pii/decrypt" -H "Content-Type: application/json" -d '{"token":"foo","justification":"bar"}')
[ "$RESP" -eq 401 ] || { echo "FAIL: Expected 401 for unauthed decrypt, got $RESP"; exit 1; }

echo "[smoke] 6/9 make sure error envelope is used"
curl -s -X POST "$BASE/v1/pii/decrypt" -H "Content-Type: application/json" -d '{"token":"foo","justification":"bar"}' | grep -q '"success":false' || { echo "FAIL: Missing error envelope"; exit 1; }

echo "[smoke] 7/9 campaign listing works (may be empty)"
curl -sf "$BASE/v1/campaigns/" | grep -q '"success":true' || { echo "FAIL: Campaign list failed"; exit 1; }

echo "[smoke] 8/9 admin stats works (authed as admin)"
# First login as admin
TOKEN=$(curl -s -X POST "$BASE/v1/auth/login" -H "Content-Type: application/json" -d '{"email":"admin@kavach.local","password":"admin"}' | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4 2>/dev/null || echo "")
if [ -n "$TOKEN" ]; then
  curl -sf -H "Authorization: Bearer $TOKEN" "$BASE/v1/admin/stats" | grep -q '"success":true' || { echo "FAIL: Admin stats failed"; exit 1; }
else
  echo "[smoke] 8/9 SKIPPED (no admin login — seed first)"
fi

echo "[smoke] 9/9 campaign brief on non-existent campaign returns 404"
RESP=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/v1/campaigns/00000000-0000-0000-0000-000000000000/brief")
[ "$RESP" -eq 404 ] || { echo "FAIL: Expected 404 for missing campaign brief, got $RESP"; exit 1; }

echo "[smoke] PASS"
