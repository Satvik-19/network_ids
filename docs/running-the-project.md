# Installation and operation

## Requirements

- Python 3.10 (the verified environment used Python 3.10.11).
- Node.js/npm compatible with the committed lockfile; `npm ci` is the reproducible frontend install.
- CPU-only machine; GPU is not required.
- Compatible local serialized inference artifacts: `ml/artifacts/supervised_model.joblib` and `ml/artifacts/isolation_forest.joblib`. These binaries are ignored/not tracked. Their JSON metadata and feature contract are tracked.
- CICIDS2017 derivative access is needed to rebuild models or rerun dataset evaluation, but not to replay already committed scenario fixtures once artifacts are present.

The project is a local single-process demonstration. It has no authentication and should not be exposed as a public service.

## Create environments and install

From the repository root in PowerShell:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Set-Location frontend
npm ci
Set-Location ..
```

`requirements.txt` is the project install list. `requirements-lock.txt` is a captured environment snapshot with packages unrelated to this app; it is not a curated cross-platform lockfile and includes an editable external repository, so do not use it as the default installation command.

## Model artifacts

A clean clone may report model unavailable because estimator binaries are not committed. The backend error message points to `ml/training/train_final_supervised.py` and `ml/training/train_isolation_forest.py`. Recreating them requires the pinned dataset splits and generated `data/processed/dev_random_train.parquet`; training scripts overwrite model artifacts and result JSON/config values. Before doing so, inspect the relevant script and preserve the currently committed evidence. Do not claim that metadata JSON alone is sufficient for inference.

The initial Phase-1 artifacts under `ml/artifacts/inference/` are not a substitute for the current Phase-2 model, because the predictor loads the top-level Phase-2 supervised and IF binaries. If supplied model binaries do not match committed metadata, the observed outputs/results are not reproducible evidence for those bytes.

## Database

SQLite is initialized automatically when FastAPI starts. Default: `data/network_ids.db`. To use a disposable database, set `NETWORK_IDS_DB` before process startup:

```powershell
$env:NETWORK_IDS_DB = "$env:TEMP\network_ids_demo.db"
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

The variable is read when the database module imports. Restart the process after changing it. Keep local database files out of commits.

## Start services

Backend terminal from the repository root:

```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Frontend terminal from repository root:

```powershell
Set-Location frontend
npm run dev
```

Open the Vite URL (normally `http://localhost:5173`). FastAPI Swagger UI is `http://127.0.0.1:8000/docs`; health is `http://127.0.0.1:8000/api/health`. Health can respond while reporting `readiness: unavailable`; verify `model_loaded: true` before running inference or replay. Stop each process with Ctrl+C.

## Evaluate or prepare scenario data

Existing evaluation artifacts can be read without retraining. The frozen shared-cohort comparison is run with:

```powershell
python -m ml.evaluation.evaluate_hybrid
```

This command requires local model artifacts and pinned source data and writes `ml/evaluation/results/locked_hybrid_random.json`; inspect/backup intentional local changes before running. The final-model and IF scripts can retrain and overwrite artifacts/results/config, so they are not routine verification commands. Scenario preparation scripts alter fixture files; do not run them unless intentionally rebuilding and reviewing fixture provenance. Details are in `docs/machine-learning/evaluation.md` and `docs/EVALUATION_PROTOCOL.md`.

## Troubleshooting

| Symptom | Check |
|---|---|
| Health says model unavailable | Confirm both Phase-2 `.joblib` files and supervised metadata exist and feature order matches; model binaries are not in a clean clone. |
| Replay start returns 503 | Model artifacts or predictor/config failed to load; inspect backend log and `/api/health`. |
| Frontend shows backend unreachable | Start backend on port 8000; Vite proxies `/api` to it. |
| Replay says busy/409 | Check polled replay state; pause/resume/stop according to state and allow prior worker to exit before starting another. |
| Playground result unavailable | Check model readiness, profile/run ID and server logs; result reads are keyed by saved numeric run ID. |
| SQLite locked/unexpected old data | Stop duplicate backend processes; point `NETWORK_IDS_DB` to a disposable path before import/start. Do not delete project data without first preserving it. |
| Vite dependency mismatch | Use `npm ci` from `frontend/` so package-lock versions are installed. |

For user workflows, see [frontend and Playground guide](frontend-and-playground.md); for exact API payloads, see [backend reference](backend-reference.md).
