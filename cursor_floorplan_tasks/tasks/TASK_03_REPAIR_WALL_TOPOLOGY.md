# TASK 03 — Repair Wall Topology

## Goal
Improve wall continuity so the structure can support reliable exterior/interior separation.

## Target file
`src/step03_repair_wall_topology.py`

## Why this task exists
The raw structural detections may contain fragmented walls, micro-gaps, small isolated components, or imperfect continuity. Flood fill depends on better structural closure.

## Input
- `output/step02/raw_structure_mask.npy`

## Required behavior
Operate only on the wall layer and:
- bridge short wall gaps,
- connect very near wall segments when reasonable,
- preserve diagonal walls,
- remove tiny isolated wall fragments,
- avoid aggressive deformations.

## Outputs
- `output/step03/repaired_wall_mask.npy`
- `output/step03/repaired_wall_mask.png`
- `output/step03/wall_diff.png`
- `output/step03/wall_repair_report.txt`

## Acceptance criteria
- wall continuity improves,
- diagonal walls remain valid walls,
- the repair does not create absurd closures,
- the diff output is understandable.

## Suggested implementation notes
- Start conservative.
- Prefer small deterministic rules over heavy heuristics.
- Make all gap/fragment thresholds configurable.

## Manual test
1. Compare raw wall vs repaired wall previews.
2. Check that obvious broken wall runs improved.
3. Confirm diagonals still exist.
4. Confirm the repair did not create impossible room closures.
