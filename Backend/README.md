# Python API

## Implemented routes

| Method | Route | Behavior |
|---|---|---|
| `GET` | `/api/health` | Return service health. |
| `GET` | `/api/hardware-profile` | Report host CPU, RAM, disk, Python/PyTorch, and visible accelerator details. Unknown hardware remains unknown. |
| `GET` | `/api/workspace` | Read project, run, dataset, evaluation, and hardware summaries from local SQLite. |
| `GET` | `/api/models?query=&limit=20&cursor=` | Search the public Hugging Face model catalog with validated pagination cursors. |
| `POST` | `/api/estimates` | Return a duration range when workload size and measured throughput are supplied; otherwise return missing calibration inputs. |
| `POST` | `/api/datasets/import` | Stream, validate, hash, and store supported JSONL/text datasets. The optional `role` form field can mark held-out data. |
| `POST` | `/api/projects` | Validate and persist a project in SQLite. |
| `POST` | `/api/evaluations` | Validate a completed run and held-out dataset. Since no evaluation worker exists, records a clear failed status and generates no fake metrics. |
| `GET` | `/api/evaluations/{id}` | Read a stored evaluation result/status. |

Training-run execution is not implemented; this API does not launch the existing training scripts.

## Run locally

Install dependencies from the workspace root:

```powershell
python -m pip install -r Backend/requirements.txt
```

Start the backend from the workspace root:

```powershell
uvicorn app:app --app-dir Backend --reload --host 127.0.0.1 --port 8000
```

Start the frontend in another terminal:

```powershell
npm --prefix frontend run dev
```

The frontend calls `http://127.0.0.1:8000`. Project and dataset records are stored under `Backend/data/` unless `LOCAL_FOUNDRY_DB_PATH` or `LOCAL_FOUNDRY_DATASET_DIR` is set.

## Tests

Run the backend suite from `Backend/`:

```powershell
python -B -m unittest discover -s tests -v
```

## Execution limitations

This is local SQLite and filesystem storage. Those are persistent for local Uvicorn use but may be ephemeral in a serverless runtime; a durable database/object-storage adapter is required before deployment there. Model training and evaluation are long-running and require a separate worker; the API does not run those jobs inline. No cloud provider has been selected or deployed.