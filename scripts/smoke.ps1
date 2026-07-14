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

Write-Host "[smoke] 4/6 auth/login (wrong creds) -> 401"
try {
    $null = Invoke-RestMethod -Method Post -Uri "$BASE/v1/auth/login" -ContentType "application/json" -Body '{"email":"fake@fake.com","password":"fake"}'
    Write-Host "FAIL: Expected 401 for bad login"; exit 1
} catch {
    if ($_.Exception.Response.StatusCode.value__ -ne 401) { Write-Host "FAIL: Expected 401 for bad login, got $($_.Exception.Response.StatusCode.value__)"; exit 1 }
}

Write-Host "[smoke] 5/6 pii/decrypt (unauthed) -> 401"
try {
    $null = Invoke-RestMethod -Method Post -Uri "$BASE/v1/pii/decrypt" -ContentType "application/json" -Body '{"token":"foo","justification":"bar"}'
    Write-Host "FAIL: Expected 401 for unauthed decrypt"; exit 1
} catch {
    if ($_.Exception.Response.StatusCode.value__ -ne 401) { Write-Host "FAIL: Expected 401 for unauthed decrypt, got $($_.Exception.Response.StatusCode.value__)"; exit 1 }
    $body = $_.Exception.Response.GetResponseStream()
    $reader = New-Object System.IO.StreamReader($body)
    $responseBody = $reader.ReadToEnd()
    
    Write-Host "[smoke] 6/6 make sure error envelope is used"
    if ($responseBody -notmatch '"success":false') { Write-Host "FAIL: Missing error envelope in $responseBody"; exit 1 }
}

Write-Host "[smoke] PASS"
