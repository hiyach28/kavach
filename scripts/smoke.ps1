# KAVACH smoke suite (Windows/PowerShell) — mirrors scripts/smoke.sh
# Grows one assertion per feature (docs/06 §1.2). Phase 0 scope: boot + health + llm-mode guard.
$ErrorActionPreference = "Stop"
$BASE = if ($env:BASE) { $env:BASE } else { "http://localhost:8000" }

Write-Host "[smoke] 1/3 liveness"
$h = Invoke-RestMethod "$BASE/health"
if ($h.status -ne "ok") { Write-Host "FAIL: liveness"; exit 1 }

Write-Host "[smoke] 2/3 readiness (postgres+redis)"
$d = Invoke-RestMethod "$BASE/health/deep"
if ($d.status -ne "ok") { Write-Host "FAIL: deep health degraded: $($d | ConvertTo-Json -Compress)"; exit 1 }

Write-Host "[smoke] 3/3 llm mode guard (must not be live outside demo)"
if ($h.llm_mode -notin @("mock", "replay")) { Write-Host "FAIL: LLM_MODE=live outside demo!"; exit 1 }

Write-Host "[smoke] PASS"
