# floorplan2

Automatic floorplan detection and alarm device placement.

Python pipeline: rasterize a floorplan, build structure/room matrices, optional **Streamlit review** (entry, electric board, struct paint), then **alarm planning** via bundled `acala_engine`.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Run the unified final steps:

```bash
PYTHONPATH=src python run_final_pipeline.py
```

After step04, open the review UI:

```bash
PYTHONPATH=src streamlit run src/matrix_review_app.py
```

Save `review_approved.json`, then step05 (or re-run the orchestrator) produces:

- `output/final/step05/final_floorplan_grid.json` — reviewed struct + rooms
- `output/final/step05/installation_proposal.json` — device plan

Generated artifacts under `output/` are not tracked (see `.gitignore`).

## Layout

- `src/final_step*.py` — main pipeline steps
- `src/matrix_review_app.py` — human review
- `vendor/acala_engine` — alarm planner library
- `config/pipeline_config.json` — cell size and thresholds

See `docs/` for architecture and specs.
