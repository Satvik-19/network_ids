# AGENTS.md — Mandatory Entry Point for Every AI Coding Agent

This file is the **single entry point** that every AI coding agent (GLM-5.2,
GLM-5-Turbo, Codex, OpenCode, etc.) must read at the start of every session
before touching any project code.

It is intentionally short. Read it fully every time.

---

## 0. First Rule

**The PRD (`Network_IDS_Security_Evaluation_PRD.md`) is the single source of
truth for the entire project.**

Read the **entire** PRD before writing, modifying, deleting, installing,
generating, refactoring, or implementing ANY project code. Do not skim.

The PRD outranks your preferences, framework conventions, tutorials, GitHub
reference repos, and previous-agent assumptions.

This is a **student-scale, CPU-friendly, reproducible academic project**.
Correctness, evaluation quality, explainability, maintainability, and
reproducibility matter more than production infrastructure.

---

## 1. Read Order (every session)

1. `AGENTS.md` (this file)
2. `Network_IDS_Security_Evaluation_PRD.md` (entire PRD)
3. `docs/PROJECT_CONTEXT.md` — compact orientation
4. `docs/ARCHITECTURE_LOCK.md` — decisions you must not casually change
5. `docs/IMPLEMENTATION_STATUS.md` — what exists right now
6. Current phase document: `docs/PHASES/PHASE_N.md`
7. Latest entries in `docs/HANDOFF.md` — immediate continuity
8. Relevant entries in `docs/DECISIONS.md`, `docs/BUG_LOG.md`,
   `docs/TESTING.md` only if related to your task
9. Existing implementation files you intend to touch — **before editing them**

`docs/SPRINT_LOG.md` is the permanent history; read it only when you need
historical investigation.

---

## 2. Core Rules

- **Never silently alter architecture.** If existing code conflicts with the
  PRD, STOP and document the conflict in `docs/DECISIONS.md` (or raise it)
  before changing anything.
- **Never add dependencies without necessity.** See the Dependency Rule in
  `docs/SPRINT_LOG.md` convention / PRD §50. Record each addition in the
  sprint log.
- **Never implement optional/stretch scope prematurely.** See
  `docs/ARCHITECTURE_LOCK.md` §"Explicit architecture non-goals".
- **Inspect existing files before modifying them.** Preserve public
  interfaces unless an approved change requires otherwise.
- **Test everything you change.** Implemented ≠ tested ≠ validated. Never
  describe an unexecuted test as passing.
- **Thresholds are config-driven, not magic numbers.** Initial values are
  placeholders until evaluation calibrates them (PRD §57).
- **CPU first. Reuse first. Explainability first. Evaluation first.**
  (PRD §61)
- **Record unresolved issues** in `docs/BUG_LOG.md` rather than hiding them.
- **UTF-8-safe atomic writes for governance/history files.** Any write to
  `docs/SPRINT_LOG.md`, `docs/HANDOFF.md`, `docs/IMPLEMENTATION_STATUS.md`,
  `docs/BUG_LOG.md`, `docs/DECISIONS.md`, or `docs/PHASES/*.md` must be:
  1. encode the COMPLETE new content to UTF-8 bytes BEFORE touching the
     target file (never open the target with `'w'` before the replacement
     content is ready),
  2. write to a temp file in the same directory, then `os.replace(temp,
     target)` for an atomic swap,
  3. re-read the target as UTF-8 afterwards and assert it is valid and has
     the expected content/entry count.
  Never truncate or rewrite an append-only log in place. Never include
  literal `\u`/`\U` escape text in a non-raw Python string that will be
  UTF-8 encoded (BUG-004). No backup subsystem is used; atomic replace +
  re-read verification is the safety mechanism.

---

## 3. Locked Boundaries (do NOT introduce by default)

Do not introduce: authentication, PostgreSQL, Redis, Celery, Kafka,
Elasticsearch, Kubernetes, microservices, cloud SOC, paid APIs, LLM
personalisation, deep-learning IDS models, LSTM/Transformers, SVM baseline,
Autoencoder (unless the PRD fallback condition is met), active penetration
testing, attack generation, arbitrary IP/network scanning, live traffic as a
baseline dependency, WebSockets (unless polling demonstrably fails),
additional datasets, additional ML models, or App Security Quick Check before
all core completion gates.

Full list and rationale: `docs/ARCHITECTURE_LOCK.md` and PRD §62.

Optional/stretch scope must never become a dependency of core functionality
(PRD §69).

---

## 4. Source-of-Truth Hierarchy

```text
1. PRD
   ↓
2. Approved architecture/decision records (docs/DECISIONS.md)
   ↓
3. DATA_ML_CONTRACT / API & implementation contracts
   ↓
4. Phase documentation (docs/PHASES/)
   ↓
5. Current implementation status + handoff
   ↓
6. Source code and tests
   ↓
7. Sprint history (docs/SPRINT_LOG.md)
```

If two documents disagree, compare both against the PRD, check for an approved
later decision, and document/resolve the discrepancy. Never silently pick one.

---

## 5. Agent Start Protocol

Every agent MUST, at the start of a session:

1. Read `AGENTS.md`.
2. Read the PRD (entire).
3. Identify the current project phase (from
   `docs/IMPLEMENTATION_STATUS.md`).
4. Read the current phase document `docs/PHASES/PHASE_N.md`.
5. Read `docs/IMPLEMENTATION_STATUS.md`.
6. Read the latest entries in `docs/HANDOFF.md`.
7. Inspect relevant `docs/DECISIONS.md`, `docs/BUG_LOG.md`,
   `docs/TESTING.md` before changing related code.
8. Inspect existing files before editing them.
9. State the exact task you intend to perform.
10. Verify that the task belongs to the active phase. Do not begin later-phase
    functionality merely because it is convenient (a tiny interface/schema
    decision required to prevent later integration problems is the only
    exception).

---

## 6. Agent End Protocol

Before finishing meaningful work, every agent MUST:

1. Run appropriate tests / validation.
2. Document what changed.
3. Document why it changed.
4. Document files changed.
5. Document commands executed.
6. Document validation results.
7. Record any bugs or limitations discovered (in `docs/BUG_LOG.md`).
8. Update current phase status in `docs/PHASES/PHASE_N.md`.
9. Update `docs/IMPLEMENTATION_STATUS.md`.
10. Append ONE structured entry to `docs/SPRINT_LOG.md`.
11. Update `docs/HANDOFF.md` with the context the next agent needs.
12. Leave the repository in a reproducible state.

An agent that changes meaningful project state without updating the
handoff/status/sprint log has **not** completed its task. The repository
documentation is the only communication channel between agents — never assume
access to another model's hidden conversation.

---

## 7. Data & ML Discipline (PRD §29–34, §47)

Always record: dataset identity/version, configuration, split, sample size,
sampling strategy, random seed, labels, transformations, feature order, model
parameters, evaluation conditions, metrics, artifact metadata.

- Do not report only accuracy.
- Do not choose the final classifier solely by accuracy.
- Do not contaminate train/test sets.
- Do not fit preprocessing using held-out test data.
- Do not silently change sampling between experiments.
- Do not silently remove minority classes.
- Do not assume the label hierarchy before inspecting the actual cleaned
  label set.
- Random and temporal evaluations must remain distinct experiments.

See `docs/DATA_ML_CONTRACT.md` for the canonical implementation-level
contract. Do not invent values before dataset inspection proves them — use
`TBD — requires validation`.

---

## 8. Git Discipline (PRD §55)

Never commit: complete CICIDS2017 datasets, virtual environments,
`node_modules`, secrets, generated cache files, or unnecessary large model
artifacts. `.gitignore` reflects this. Do not perform destructive Git
operations unless explicitly asked. Do not overwrite unrelated user changes.

---

## 9. Implementation Documentation Vocabulary

Be precise. These words mean different things:

- **Planned** — not implemented.
- **Implemented** — code exists.
- **Tested** — specific validation has run.
- **Validated** — required behaviour / completion criteria passed.

Never claim a model, endpoint, feature, dataset transformation, metric, or UI
component exists merely because it appears in a plan.
