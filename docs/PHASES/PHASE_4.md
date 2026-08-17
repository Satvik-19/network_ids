# Phase 4 — Personalised Security Playground

Source: PRD §58 (Phase 4), §18–24, §44, §45. Active only after Phase 3 gate
passes.

## Goal

Build the differentiating interactive layer — personalised, rule-based
security evaluation — WITHOUT increasing ML complexity.

## PRD Scope

**Questionnaire (PRD §19):** deliberately short.
- Environment Type: Personal/Home, College/Lab, Small Organisation,
  Web Application/Server Environment.
- Approximate Scale: 1–10, 10–50, 50+ devices.
- Internet Exposure: internal only / some public services / public-facing.
- Services: Web/HTTP(S), SSH, FTP, Database, File sharing.

**Rule-based scenario generation (PRD §20, §44):** no LLM.
- SSH enabled → SSH brute-force scenario.
- FTP enabled → FTP brute-force scenario.
- Public web → web-attack scenario.
- Public-facing / larger network → DDoS scenario.
- Multi-device → Port Scan / reconnaissance.
- Always → unknown anomaly scenario.

**Scenario library (PRD §45):** `data/scenarios/{ddos,port_scan,
ssh_bruteforce,ftp_bruteforce,web_attack,botnet,benign,unknown_anomaly}/`
with held-out representative flows + expected metadata. The unknown scenario
must be built via a controlled experiment, NOT fake "zero-day" claims
(PRD §45, §46).

**Execution (PRD §21):** prepared scenario flows pass through the exact same
final hybrid pipeline.

**Readiness report (PRD §22, §23, §24):**
- Readiness score (0–100) derived primarily from actual test outcomes; exact
  weights configurable.
- Blind-spot detection = weakest tested area, derived from results.
- Visuals: readiness score, scenario result matrix, risk distribution,
  known-vs-unknown coverage, strongest area, blind spot.
- PDF export optional — must not block completion.

## Explicitly Out of Scope During This Phase

- LLM-based personalisation (PRD §20).
- Any scanning or attack generation against user-supplied IPs/networks
  (PRD §18, §54).
- Model Evaluation Lab UI (Phase 5).
- App Security Quick Check (stretch, after all core gates — PRD §53).

## Required Deliverables (PRD §58 Phase 4)

- Playground page.
- Scenario generator.
- Personalised test results.

## Implementation Tasks

- [ ] Build the environment questionnaire UI.
- [ ] Implement rule-based scenario selector (PRD §20).
- [ ] Prepare held-out scenario sample sets with expected metadata.
- [ ] Build the controlled unknown-anomaly scenario (per PRD §46 choice).
- [ ] Implement the test runner (reuse the final hybrid pipeline).
- [ ] Implement readiness scoring (configurable weights).
- [ ] Implement blind-spot detection from results.
- [ ] Build the visual readiness report (Recharts).
- [ ] (Optional) PDF export — do not let it block the gate.

## Dependencies / Prerequisites

- Phase 3 complete (final hybrid pipeline + incident/visual infrastructure).
- Held-out scenario data not contaminating training/test sets (PRD §45, §46).

## Files / Components Expected (PRD §55)

- `data/scenarios/<scenario>/`.
- `backend/app/services/playground/`.
- `backend/app/api/` (`/api/playground/*`).
- `frontend/src/pages/` (Playground).

## Validation Plan

- Different profiles produce different logical suites (Phase-4 gate).
- Readiness score and blind spot are derived from actual outcomes (no fake
  metrics).
- Scenario flows are truly held-out (no train/test leakage).
- Playground tests in `docs/TESTING.md` §9.

## Completion Gate (PRD §58)

Different profiles produce different logical test suites.

```text
College Lab → SSH + Port Scan + DDoS + anomaly
Web Server  → Web Attack + DDoS + brute force + anomaly
```

## Completion Gate Evidence

`TBD — fill when gate passes`.

## Current Status

NOT STARTED.

## Blockers

None (awaiting Phase 3 completion).

## Decisions Made During This Phase

(Record: scenario selection rules, readiness weights, blind-spot logic,
unknown-anomaly experiment choice, held-out data provenance.)
