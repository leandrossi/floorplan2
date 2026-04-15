# Project Context

## Project name
Floorplan to Matrix Pipeline (final unified flow)

## Core objective
Convert a floorplan image into two machine-usable matrix outputs, then optionally plan alarm device placement.

### Output A — Structural matrix
Cell meaning:
- `0 = exterior`
- `1 = wall`
- `2 = window`
- `3 = door`
- `4 = interior`

### Output B — Room-id matrix
Cell meaning:
- `0 = not-a-room / exterior / structure`
- `1..N = room_id`

## What the project is solving
1. Detect walls, windows, doors, and room regions (via **one** unified Roboflow workflow).
2. Rasterize and classify space (exterior vs interior vs openings).
3. Assign room ids from topology, assisted by room polygons.
4. Export final matrices and human-review bundle.
5. Run deterministic alarm planning (`vendor/acala_engine`) on the reviewed grid.

## What is NOT in scope right now
- OCR of room labels,
- semantic room naming (`kitchen`, `bathroom`, etc.),
- full CAD reconstruction,
- perfect architectural vectorization,
- production optimization.

## Current data source
A **single** Roboflow serverless workflow produces `output/result_workflow_final.json` with both structural (bbox-style) and room (polygon) predictions in one document. See `run_workflow_final.py` and `roboflow_workflow_common.py`.

### Structural usage
Primary geometric truth for walls, windows, doors, and layout closure.

### Room usage
Proposes room regions and helps assign ids; it must not replace topological segmentation from structure.

## Closed interpretation rules
### Structural source of truth
The structural detections drive enclosure and interior/exterior separation.

### Room run usage
Used to propose and validate room regions only.

### Diagonal class
`diagonal` must be treated as `wall`.

### Doors for room segmentation
Doors are treated as temporarily closed so adjacent rooms do not merge incorrectly.

## Main engineering philosophy
- one file per pipeline stage (`final_step*.py`),
- visible output per stage under `output/final/stepNN/`,
- deterministic behavior,
- easy manual validation,
- easy debugging.

## Success criteria for this stage
- Structural matrix is coherent; diagonal walls are walls.
- Exterior/interior separation is plausible.
- Room ids are consistent per region.
- Step05 alarm outputs are generated without engine errors for typical inputs.
