# floorplan2

Automatic floorplan detection and alarm device placement.

Python pipeline: Roboflow unified JSON → rasterize and build structure/room matrices → **Streamlit wizard** (entry, electric board, struct paint) → **alarm planning** via bundled `acala_engine`.

## Local Quick Start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Create a local `.env` file with:

```bash
ROBOFLOW_API_KEY=your_roboflow_key
```

### Main Entry (Wizard)

Upload a floorplan image (or use existing `output/result_workflow_final.json`), run steps 01–04, review, then step05:

```bash
PYTHONPATH=src:vendor/acala_engine/src streamlit run src/app.py
```

Local wizard artifacts are written to `workspaces/` by default. This directory is ignored by git.

### Production-Style Local Smoke Test

This runs the same command shape used by a persistent cloud host:

```bash
export PORT=8501
export APP_WORKSPACES_ROOT=/tmp/floorplan-workspaces
export PYTHONPATH=src:vendor/acala_engine/src
streamlit run src/app.py --server.address=0.0.0.0 --server.port=$PORT --server.headless=true
```

### Headless Pipeline

If you already have `output/result_workflow_final.json` (e.g. from `python run_workflow_final.py <image.png>`):

```bash
PYTHONPATH=src:vendor/acala_engine/src python run_final_pipeline.py
```

After step04, the orchestrator prints a reminder: open the wizard to place markers and save `review_approved.json` under `output/final/step04/`, then re-run step05 or run the full orchestrator again.

Step05 outputs include:

- `output/final/step05/final_floorplan_grid.json` — reviewed struct + rooms
- `output/final/step05/installation_proposal.json` — device plan

Generated artifacts under `output/` are not tracked (see `.gitignore`).

## Production Test Deployment

This project is a Streamlit application with long-running Python processing, custom Streamlit components, subprocess execution, and per-session file artifacts. Use a persistent Python web service such as Render, Railway, Fly, or Streamlit Community Cloud for testing. Do not deploy this Streamlit app directly to Vercel serverless functions.

The repo includes `render.yaml` for a Render-style persistent web service:

- Build command: `pip install -r requirements.txt`
- Start command: `PYTHONPATH=src:vendor/acala_engine/src streamlit run src/app.py --server.address=0.0.0.0 --server.port=$PORT --server.headless=true`
- Temporary test storage: `APP_WORKSPACES_ROOT=/tmp/floorplan-workspaces`

Required production environment variables:

```bash
ROBOFLOW_API_KEY=your_roboflow_key
APP_WORKSPACES_ROOT=/tmp/floorplan-workspaces
```

For the first online test, uploads and generated outputs are temporary. They can disappear when the service restarts or is redeployed. If persistent customer data is needed later, move uploads/results to object storage and store session metadata in a database.

## Layout

- `src/final_step*.py` — main pipeline steps
- `src/app.py` — end-to-end Streamlit UI (Roboflow + review + step05)
- `run_workflow_final.py` — Roboflow CLI for `result_workflow_final.json`
- `run_final_pipeline.py` — subprocess runner for final steps 01–05
- `vendor/acala_engine` — alarm planner library
- `config/pipeline_config.json` — cell size and thresholds

See `docs/` for architecture and specs.
