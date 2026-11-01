# Testing and verification

This is a documentation update. The verification recorded here separates previously executed application evidence from documentation checks run for this documentation change. A source-code test is not claimed to have run merely because it appears in an earlier phase record.

## Project test commands

Run from the repository root unless noted:

```powershell
python -m pytest ml/tests backend/tests -q -p no:cacheprovider --tb=short
```

From `frontend/`:

```powershell
npm test
npm run build
```

The build runs TypeScript project build and Vite production bundling. A standalone compiler check used in the UI redesign was:

```powershell
node node_modules/typescript/bin/tsc --noEmit --incremental false
```

To exercise the live replay integration gate, with model artifacts/dependencies present:

```powershell
python -m backend.tests.e2e_replay_phase3
```

That gate writes its evidence to a committed result path by default; if protecting historical evidence, inspect the module and direct its output to a temporary path as done in the recorded run. Browser workflows require a running backend and Vite server. Do not treat a frontend build as browser validation.

## Coverage map

| Area | Existing validation |
|---|---|
| Labels/preprocessing | `ml/tests/test_preprocessing.py` |
| Metrics/evaluation | `ml/tests/test_evaluation.py` |
| Hybrid and risk | `ml/tests/test_hybrid.py` |
| Predictor contract | `ml/tests/test_predictor.py` |
| Native SHAP | `ml/tests/test_shap.py` |
| API | `backend/tests/test_api.py` |
| Replay worker and failures | `backend/tests/test_replay.py`, `test_replay_failures.py`, `test_replay_api.py` |
| Incident grouping | `backend/tests/test_incidents.py` |
| Scenario schema | `backend/tests/test_scenarios.py` |
| Playground rules/API/readiness/history | `test_playground.py`, `test_playground_api.py`, `test_readiness.py`, `test_threshold_history.py` |
| UI helper regressions | `frontend/tests/*.test.mjs` via `npm test` |
| UI type/build | `npm run build` |

## Previously recorded implementation verification

`docs/TESTING.md`, `docs/IMPLEMENTATION_STATUS.md` and `docs/SPRINT_LOG.md` record the full application validation executed on 2026-10-31. The most recent pre-documentation UI redesign record reports 142 Python tests passing in 226.99 seconds, 10 frontend Node tests passing, standalone TypeScript and Vite production build passing, the original live-Uvicorn replay gate passing with temporary evidence output, and browser review of current screens. The build retained a >500 kB chunk warning. Hue validation reported zero errors/warnings and one Windows `npx` subprocess skip, covered by independent strict YAML parsing. Those are historical test results, not runs made by this documentation audit.

The project includes an intentionally difficult network/dataset-dependent test suite. Rerun it in the intended pinned environment before a software release or if source/model behavior changes. Browser review should exercise both light/dark themes and desktop/narrow layouts. Current application/replay results and the design evidence are in [TESTING.md](TESTING.md) and [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md).

## Documentation checks executed 2026-11-01

- Final repeat check covered 28 README/docs Markdown files as UTF-8; fenced blocks balanced and all local links/anchors resolved, including newly created files.
- Strict duplicate-key YAML parsing of `config/config.yaml` passed. All scenario, evaluation-result and artifact JSON files parsed.
- FastAPI `app.openapi()` exposed the 15 expected documented paths/methods. Seven fixtures, 52 flow rows and exactly 77 features per row were asserted.
- `python -m pytest ml/tests/test_hybrid.py backend/tests/test_incidents.py backend/tests/test_scenarios.py -q -p no:cacheprovider --tb=short`: **41 passed in 4.87s**.
- Full command `python -m pytest ml/tests backend/tests -q -p no:cacheprovider --tb=short` was attempted but did not complete. `-x` reproduced the first failure: `ml/tests/test_predictor.py::test_predict_full_contract` cannot resolve the remote dataset host (`socket.gaierror: [Errno 11001] getaddrinfo failed`) while `load_split()` reads the pinned Hugging Face Parquet. `ml/tests/test_shap.py` fixture setup fails for the same remote DNS dependency. This is an environment/network limitation; the complete suite result is **unverified in this pass**. Earlier 142-pass result remains dated 2026-10-31.
- In this pass, `npm test`: **10 passed**; `node node_modules/typescript/bin/tsc --noEmit --incremental false`: **exit 0**; `npm run build`: **exit 0**, with the existing 564.73 kB minified chunk warning.
- Mermaid fences and diagram sources are present, but no Mermaid renderer was available; rendering is **unverified**. Git diff/check and remote publication state are recorded in the handoff/commit review, not inferred from these checks.

These are documentation and targeted verification results. No model was trained, evaluation JSON regenerated, or application code changed.
