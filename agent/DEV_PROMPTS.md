# DEV_PROMPTS.md — Prompt Playbook for Developer + Claude Pairing

How to use: start every session with the **Session Opener**, then use the phase prompt for where you are in `ROADMAP.md`. These prompts are written to make Claude collaborate — propose, explain, and check in — rather than dump code.

---

## Session Opener (paste at the start of every session)
```
Read CLAUDE.md, ROADMAP.md, and FEATURE_STATUS.md. Confirm LLM_MODE is mock
or replay. Tell me:
1) which phase we're in, and implemented vs pending per FEATURE_STATUS.md,
2) the single highest-leverage task to do next and why (cite its F-ID and
   its spec section in docs/04_FEATURE_DETAILS.md),
3) your plan for it in ≤6 bullets.
Wait for my go-ahead before writing code.
```

## Session Closer
```
Before we stop: update FEATURE_STATUS.md rows you touched (status, test IDs,
notes), run `make smoke` and report the result, list any hard-rule risks
(CLAUDE.md), any TODOs left in code, and a 3-line handoff note. Confirm no
live LLM calls were made this session (or list them with cost).
```

## Phase-End Regression (paste at every phase boundary — the never-break check)
```
Execute docs/06_TESTING_AND_STABILITY.md §2 verbatim: full test suite, fresh-
clone smoke, eval regression, Playwright (if Phase ≥4), AND re-run every
previous phase's gate checklist. Report each item pass/fail honestly, log the
result in FEATURE_STATUS.md Gate Log with git SHA. A single red item = we fix
before the next phase, no exceptions. Do not start next-phase work.
```

## Design-decision prompt (any fork in the road)
```
We need to decide: <decision>. Give me 2–3 options with: effort, risk,
reversibility, and impact on the phase gate. Recommend one and say what
you'd need from me to proceed. Don't implement yet.
```

## Code-review prompt (after any large chunk)
```
Review the diff you just produced as a hostile hackathon judge with security
expertise. Check specifically against docs/03_SECURITY.md and the hard rules
in CLAUDE.md. List findings by severity; fix criticals; ask me about the rest.
```

---

## Phase prompts

### Phase 0 — Reset
```
Execute Phase 0 of ROADMAP.md. Propose the exact repo tree, tooling configs
(ruff, mypy, pytest, eslint, pre-commit) and CI workflow before creating
anything. Port from legacy/ ONLY: llm schemas+prompts, deidentify.py,
clustering.py, ForceGraph.jsx, tokens.css — into legacy/ untouched.
Gate G0 must pass before you report done.
```

### Phase 1 — Secure core
```
Phase 1. Start with the authz test matrix (every planned endpoint × 4 roles,
expected status codes) as failing tests — show me the matrix first. Then
implement auth, RBAC, PII vault, and audit chain to make it pass. Walk me
through the envelope-encryption flow with a diagram before coding the vault.
Gate: G1 checklist, plus show me a raw DB dump proving zero plaintext PII.
```

### Phase 2 — Async pipeline
```
Phase 2. Before coding: sketch the worker job graph (job names, payloads,
retry policies, idempotency keys) and the case status state machine. I want
to review both. Then implement in this order: queue plumbing → LLM client
with fallback chain → entity extraction → pgvector ANN → incremental
clustering. After each step, run the 5k-case seed and report timings against
Gate G2 numbers.
```

### Phase 3 — Shield
```
Phase 3. The live-call companion is the demo centerpiece — prototype it
end-to-end (even ugly) in the first day so we can de-risk browser STT, then
harden. For the check endpoint, show me the decision cascade (lookup → ANN →
LLM) with expected latency per tier before implementing. Localization: build
the template system, then we'll write hi/ta/te/bn copy together — flag any
string you machine-translate so I can have it human-checked.
```

### Phase 4 — Terminal UI
```
Phase 4. Follow agent/DESIGN_REFERENCE.md strictly — tokens only, no ad-hoc
styles. Build shell → Overview → FraudScope → NetworkX → CrimeMap → Evidence
Locker, in that order, and stop for my review after each view. Every view
needs empty/loading/error states. The four "signature moments" in the design
doc get extra polish — treat them as their own tasks.
```

### Phase 5 — Hardening
```
Phase 5. Write the locustfile and run load tests; report p50/p95/p99 per
endpoint vs. Gate G5 targets. Then chaos drills (kill LLM, kill worker,
restart PG) — document observed behavior honestly, fix what breaks. Then the
security suite from docs/03 §7. Finally build the 200-case eval benchmark and
produce the precision/recall/FP table. No greenwashing: red numbers get
reported as red.
```

### Phase 6 — Submission assets
```
Phase 6. Draft the demo video script from docs/01 §6 with timestamps
(≤5 min), a shot list, and the seeded data needed for each beat. Then the
submission document skeleton and deck outline from ROADMAP.md Phase 6.
I'll record; you prepare every screen state so no step can fail live.
```

---

## Recovery prompts

**When Claude went too far without checking in:**
```
Stop. Summarize everything you changed since my last approval, in a table:
file / change / risk. We review before anything else happens.
```

**When something is broken and unclear:**
```
Debug systematically: reproduce → isolate (binary-search the cause) → explain
root cause → propose minimal fix + regression test. Narrate each step; don't
jump to a fix you can't justify.
```

**When scope is creeping:**
```
Check this idea against ROADMAP.md and the phase gate. Is it needed for the
current gate? If not, add it to a PARKED.md with a one-line rationale and
return to the gate task.
```
