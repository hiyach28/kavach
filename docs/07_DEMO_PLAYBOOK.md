# KAVACH v2 — Demo Video Playbook

Target: ≤5 minutes, judges' four criteria hit in order of weight. Every claim on screen has its number visible (doc 05 §5 rule: never say a stat without showing its source). Script drafted in Phase 4, screens frozen in Phase 5, recorded in Phase 6 after 3 clean rehearsals.

**Format:** screen capture (Terminal, 1080p) + phone footage (Shield, stabilized) + one Grafana cut. Voiceover from script below. No music over the live-call beat — the tension IS the demo.

---

## Beat sheet

### D-0 · Cold open — the problem (0:00–0:25)
On-screen: one stat card, then the phone ringing.
VO: "In 2024, digital-arrest scams alone stole over ₹1,776 crore from Indian citizens. 123,000 reported incidents. Every existing tool starts working *after* the money is gone. KAVACH starts before."

### D-1 · Live interception — Shield (0:25–1:30) ★ centerpiece
Phone footage. A volunteer receives the scripted "CBI officer" call (script = the committed test fixture, doc 04 F33). They tap "I'm on a suspicious call."
- Show: transcript streaming → amber caution at the impersonation stage (~20s) → full-screen red DANGER at the payment demand, advice in **Hindi**.
- Stats shown on screen: verdict latency stopwatch overlay; "this pattern: 23 linked reports" from the entity lookup.
- VO closes: "That warning fired before a single rupee moved — in the caller's own language."

### D-2 · From interception to intelligence — FraudScope (1:30–2:15)
Cut to Terminal. The intercepted attempt arrives as a case; show the live pipeline ticker (queued→classifying→clustered).
- Show: PII-masked text side-by-side with original (F13), red flags with highlighted evidence substrings, reasoning trace, entity panel ("UPI seen in 14 reports, 3 states").
- Stat moment: 2s zoom on the Model Quality KPI card → click through to eval tab: precision/recall/**FP-rate <2%** table on the 200-case benchmark + trend line across eval runs ("accuracy improves with every analyst correction").

### D-3 · The ring emerges — NetworkX (2:15–3:00)
- Show: new case node drops into the graph with pulse animation, auto-links into a 23-case campaign via shared mule UPI; toggle a **semantic edge** — "these two cases share zero phone numbers, but the same script. Louvain clustering catches the ring anyway."
- Temporal scrubber: replay the campaign growing over 3 weeks in 5 seconds.

### D-4 · Early warning (3:00–3:25)
Scripted burst fixture fires the amber banner live on camera.
- Show: "Campaign #7 velocity 4.1× baseline — projected 40 victims/week", with the lead-time figure inside the alert ("first alert 41 min after burst onset").
- VO: "KAVACH flags mass-victimisation while it's ramping — not in next quarter's crime statistics."

### D-5 · Takedown brief (3:25–3:50)
Officer view. Open the brief: top target entity, "seize this account → network connectivity falls 71%", ranked top-5.
- VO: "The graph doesn't just visualize the ring. It tells you where to strike first."

### D-6 · Court-ready evidence (3:50–4:20)
- Show: one-click evidence package build → open the ZIP: chain-of-custody log, hash manifest, draft Section 65B certificate → run `python verify.py` on camera → green. Optional 3s: tamper one byte on a copy, verify fails at the exact record.
- VO: "Every step since intake is hash-chained. This package is built for court, not just for slides."

### D-7 · Command view & scale (4:20–4:50)
- CrimeMap: toggle complaints (lagging) vs Shield-check density (leading) — "we see districts heating up before complaints arrive."
- Overview KPIs 3s. Then the Grafana cut: Locust at 100 req/s intake + 500 req/s Shield, p95 lines under targets, 100k cases seeded.
- VO: "Stateless API, queue-backed workers, Postgres with pgvector — the load test is in the repo."

### D-8 · Close (4:50–5:00)
Flywheel diagram (one slide): Shield → Intelligence → Takedown → smarter Shield.
VO: "KAVACH. Protection at the point of contact. Intelligence at the speed of the scam. — Built for ET AI Hackathon 2026."

---

## Production checklist
- [ ] All beats run off `make seed-demo` state; rehearsed 3× clean (doc 06 §5)
- [ ] Fallback recording exists per beat before live recording day
- [ ] Phone beat: airplane-mode-off spare phone ready; screen-record on device AND camera angle
- [ ] Every stat on screen traceable to doc 05 §2 definitions (judges may ask)
- [ ] `LLM_MODE=live` only during D-1/D-2 takes; budget guard active
- [ ] Captions burned in (judging rooms are loud); logo + repo URL end-card

## Submission document mirrors this
Same beats become sections: Problem → Live protection → Intelligence pipeline → Early warning → Takedown → Admissibility → Scale proof (tables from doc 05 + Phase 5 numbers) → Architecture diagram (doc 02 §1) → Roadmap beyond.
