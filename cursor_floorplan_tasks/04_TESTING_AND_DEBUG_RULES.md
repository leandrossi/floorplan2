# Testing and Debug Rules (final pipeline)

## Main rule
Every step must generate something a human can inspect: preview PNG, overlay, text report, CSV, and/or `.npy` as appropriate.

## Debug strategy
Prefer visual debugging over silent assumptions (overlays, previews, short text reports next to binaries).

## Running steps (from repo root)
Use `PYTHONPATH=src` so `pipeline_common` resolves.

**Full chain (subprocess):**
```bash
PYTHONPATH=src python run_final_pipeline.py
```

**Individual steps (examples):**
```bash
PYTHONPATH=src python src/final_step01_parse_and_rasterize.py
PYTHONPATH=src python src/final_step02_classify_space.py
PYTHONPATH=src python src/final_step03_assign_rooms.py
PYTHONPATH=src python src/final_step04_build_matrix_csv.py
PYTHONPATH=src python src/final_step05_plan_alarm.py
```

Ensure `output/result_workflow_final.json` exists before step01 (from `python run_workflow_final.py <image.png>` or the wizard).

## UI review
```bash
PYTHONPATH=src streamlit run src/wizard_app.py
```
After step04, place main entry / electric board, optional struct paint, choose security level, save `review_approved.json` under `output/final/step04/`, then run step05 (or re-run `run_final_pipeline.py`).

## Manual review checklist

### After final step01
- Structural mask: walls/windows/doors roughly match the plan?
- Room polygons: plausible regions, no huge gaps?

### After final step02
- Exterior flood-fill stays outside the building envelope?
- Interior vs openings coherent?

### After final step03
- Room ids stable per region; doors not collapsing distinct rooms?

### After final step04
- `final_structure_matrix` / `final_rooms_matrix` previews match expectations?
- `review_bundle.json` loads in the wizard?

### After final step05
- `installation_proposal.json` and device CSVs look consistent with the grid?
- `acala_engine` report has no unexpected hard failures?

## Recommendation
Validate sequentially (01 → 02 → …). Fix upstream before tuning step05.

## Pre-flight grid validation (wizard + step05)

Before `plan_installation`, the effective structure matrix (`0..4`) is checked by
`src/grid_topology_validate.py` (`validate_grid_for_alarm`: marcadores + topología).

| Código / prefijo | Severidad | Significado breve |
|------------------|-----------|-------------------|
| `INT_EXT_ADJ` | error | Interior (4) 4-vecino de exterior (0) sin barrera. |
| `EXTERIOR_ISLAND` | error | Mancha de exterior (0) sin contacto con el borde de la grilla. |
| `OPENING_NO_ADJACENT_FREE` | error | Ventana/puerta sin vecino exterior o interior. |
| `OPENING_LONG_SIDE_WALL` / `OPENING_SHORT_SIDE_FREE` | warning | Caras largas/cortas del bbox de apertura (alineado con step04 `enforce_opening_adjacency`). |
| `INTERIOR_LEAKS_TO_BORDER` | error solo si `TopologyOptions.r4_interior_reachable_without_wall=True` | Casi siempre desactivado: con puertas al borde todo el interior sería “alcanzable”. |
| `NO_INTERIOR` | error | No hay celdas interior (4). |
| `MAIN_ENTRY_NO_EXTERIOR` | error (wizard y step05 con marcadores) | Puerta principal debe ser 4-vecina de al menos un (0). |
| Errores de `validate_approved` | error | `main_entry` / `electric_board` obligatorios, bounds, `struct_patch`. |

**Step05:** si la validación falla, se escribe `alarm_plan_report.json` con `grid_validation_failed` y no se genera propuesta. Para depuración:  
`PYTHONPATH=src python src/final_step05_plan_alarm.py --skip-grid-validation`

**Tests del repo:**  
`PYTHONPATH=src python -m unittest tests.test_grid_topology_validate -v`

## Automated tests
Run alarm engine unit tests when touching planning rules or step05 integration:
```bash
cd vendor/acala_engine && pytest -q
```
