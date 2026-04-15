# floorplan2

Automatic floorplan detection and alarm device placement.

Python pipeline: Roboflow unified JSON → rasterize and build structure/room matrices → **Streamlit wizard** (entry, electric board, struct paint) → **alarm planning** via bundled `acala_engine`.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Main entry (wizard)

Upload a floorplan image (or use existing `output/result_workflow_final.json`), run steps 01–04, review, then step05:

```bash
PYTHONPATH=src streamlit run src/wizard_app.py
```

### Headless pipeline

If you already have `output/result_workflow_final.json` (e.g. from `python run_workflow_final.py <image.png>`):

```bash
PYTHONPATH=src python run_final_pipeline.py
```

After step04, the orchestrator prints a reminder: open the wizard to place markers and save `review_approved.json` under `output/final/step04/`, then re-run step05 or run the full orchestrator again.

Step05 outputs include:

- `output/final/step05/final_floorplan_grid.json` — reviewed struct + rooms
- `output/final/step05/installation_proposal.json` — device plan

Generated artifacts under `output/` are not tracked (see `.gitignore`).

## Layout

- `src/final_step*.py` — main pipeline steps
- `src/wizard_app.py` — end-to-end UI (Roboflow + review + step05)
- `run_workflow_final.py` — Roboflow CLI for `result_workflow_final.json`
- `run_final_pipeline.py` — subprocess runner for final steps 01–05
- `vendor/acala_engine` — alarm planner library
- `config/pipeline_config.json` — cell size and thresholds

See `docs/` for architecture and specs.
