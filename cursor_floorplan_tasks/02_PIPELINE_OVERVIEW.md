# Pipeline Overview (final flow)

## Summary
The shipped pipeline has **five** executable steps under `src/final_step*.py`, plus **Roboflow** for detection JSON and optional **Streamlit** (`wizard_app.py`) for human review before alarm planning.

## Ingestion
1. **Roboflow** (unified workflow): `python run_workflow_final.py <image.png>` → writes `output/result_workflow_final.json` (and optional visualization JPGs under `output/visualizations/` if enabled by the runner).
2. **Wizard** can call the same runner after an image upload, or skip API and reuse an existing `result_workflow_final.json`.

## Core steps (deterministic, local)
| Step | Script | Role |
|------|--------|------|
| 01 | `final_step01_parse_and_rasterize.py` | Parse unified JSON → structural + room polygon rasters |
| 02 | `final_step02_classify_space.py` | Exterior / interior / openings from structure |
| 03 | `final_step03_assign_rooms.py` | Room ids from topology + room proposals |
| 04 | `final_step04_build_matrix_csv.py` | Final structure + room matrices, CSVs, `review_bundle.json` |
| 05 | `final_step05_plan_alarm.py` | Alarm plan via `vendor/acala_engine`, reads `review_approved.json` if present |

## Orchestration
- **Headless:** `PYTHONPATH=src python run_final_pipeline.py` runs steps 01→05 as subprocesses (after step04, message reminds to open the wizard to save `review_approved.json` if needed).
- **UI:** `PYTHONPATH=src streamlit run src/wizard_app.py` — upload / JSON reuse → steps 01–04 → review → step05.

## High-level data flow
```text
image.png
    → run_workflow_final.py
        → output/result_workflow_final.json
            → final_step01 → output/final/step01/ (*.npy, previews)
            → final_step02 → output/final/step02/
            → final_step03 → output/final/step03/
            → final_step04 → output/final/step04/ (matrices, review_bundle.json)
            → [wizard: review_approved.json]
            → final_step05 → output/final/step05/ (proposal, CSVs, grids)
```

## Design principle
Room segmentation is built on structural topology first; room-model polygons assist assignment but do not replace flood-fill regions derived from walls/doors/windows.

## Output layers (final matrices)
### Structural (`final_structure_matrix`)
- `0` exterior, `1` wall, `2` window, `3` door, `4` interior

### Room ids (`final_rooms_matrix`)
- `0` non-room / structure / exterior
- `1..N` room ids for interior free space

Keep these layers separate until downstream consumers merge them (e.g. step05 / exports).
