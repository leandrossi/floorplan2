# TASK 04 — Build Structural Mask

## Goal
Combine repaired walls with windows and doors into a consolidated structural mask.

## Target file
`src/step04_build_structural_mask.py`

## Why this task exists
Wall repair should improve the wall layer, but windows and doors still need to be embedded back into the structure for downstream reasoning.

## Inputs
- `output/step02/raw_structure_mask.npy`
- `output/step03/repaired_wall_mask.npy`

## Required behavior
- use repaired walls as the wall base,
- recover window and door layers from the raw structure mask,
- combine all three into one structural mask,
- resolve overlaps consistently,
- produce visible debug outputs.

## Encoding
- `0 = empty`
- `1 = wall`
- `2 = window`
- `3 = door`

## Outputs
- `output/step04/structural_mask.npy`
- `output/step04/structural_mask.png`
- `output/step04/structural_overlay.png`
- `output/step04/structural_conflicts_report.txt`

## Acceptance criteria
- windows/doors are not floating disconnected from the layout,
- the structure still defines plausible regions,
- consolidated output is visually cleaner than the raw mask.

## Suggested implementation notes
- Keep class priority explicit.
- Report suspicious window/door placements if they sit far from wall context.

## Manual test
1. Inspect structural overlay.
2. Confirm windows and doors are embedded in the layout.
3. Confirm repaired walls are used.
