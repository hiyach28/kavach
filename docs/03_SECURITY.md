# KAVACH v2 — Security Requirements & Checklist

Every item below traces to a concrete v1 defect (see `00_ASSESSMENT.md`) or to the evaluation focus ("false positive rate must be very low", "auditability for legal admissibility").

## 1. Authentication & Authorization
- [ ] JWT auth (short-lived access + refresh), bcrypt/argon2 password hashing
- [ ] RBAC: `citizen` (Shield only) · `analyst` (cases, graph) · `officer` (+ PII decrypt, evidence export) · `admin` (+ users, metrics)
- [ ] District/state scoping on analyst queries (an analyst sees their jurisdiction unless granted more)
- [ ] Every privileged action → audit event; PII decryption requires justification text

## 2. Data Protection
- [ ] PII vault: AES-256-GCM per-record encryption, wrapped DEKs, master key from env/KMS — **no plaintext PII anywhere in the main DB** (fixes v1's plaintext `pii_token_map`)
- [ ] Graph and analytics tables store SHA-256 hashes of identifiers only
- [ ] De-identification runs before any LLM call (keep v1 behavior; expand patterns: emails, PAN, addresses, names via NER)
- [ ] TLS assumed at ingress; no secrets in git (CI secret-scan gate); populated `.env.example`; `.venv`/`node_modules` never committed

## 3. API Hardening
- [ ] Rate limiting: per-IP on Shield (e.g. 20/min), per-user on Terminal; global LLM budget breaker
- [ ] Input caps: complaint text ≤ 50KB, uploads ≤ 10MB with MIME sniffing, image re-encode before OCR
- [ ] Strict CORS (exact origins, methods, headers); security headers (CSP, HSTS, X-Content-Type-Options, frame-deny)
- [ ] Pydantic validation everywhere; no bare `except`; typed error envelope; no stack traces to clients
- [ ] Pagination mandatory on all list endpoints

## 4. LLM-Specific Threats
- [ ] Prompt injection: user content in delimited untrusted blocks; instruct-as-data framing; output schema validation server-side (evidence substrings must literally occur in the input, enums/ranges enforced)
- [ ] Never execute/render LLM output as HTML (XSS via verdict text); escape in UI
- [ ] Log prompts/outputs (masked) with trace IDs for forensics; per-call cost metering
- [ ] Fallback chain so a poisoned/failed provider degrades to rules-only mode, never silent failure

## 5. Evidence Integrity (differentiator)
- [ ] Append-only hash-chained `audit_chain` (DB role has INSERT only)
- [ ] Evidence packages: SHA-256 manifest, chain segment, `verify.py`, draft Section 65B(4) certificate
- [ ] Clock source noted in package (NTP), operator identity bound to export

## 6. Abuse & Misuse Cases (design for them)
- Scammer probing Shield to test scripts against the classifier → rate limits, no raw score exposure to citizens (verdict bands only), anomaly alerts on probing patterns
- False accusation risk → "indicative" language on all citizen verdicts; human review before any entity is publicly flagged; FP rate is a first-class metric
- Insider PII snooping → per-read audit + justification + admin review dashboard

## 7. Verification Gates (CI + pre-demo)
- [ ] `bandit` + `pip-audit` (backend), `npm audit` (frontend) green in CI
- [ ] Dedicated security test suite: authz matrix tests (every endpoint × every role), injection corpus tests, rate-limit tests
- [ ] Pre-demo checklist run: fresh clone → docker compose up → seeded demo → all gates pass
