# TASK 05 — Classify Exterior / Interior

## Goal
Separate free space into exterior and interior using the consolidated structural mask.

## Target file
`src/step05_classify_exterior_interior.py`

## Why this task exists
The project needs a structural matrix where free cells are classified as either exterior or interior.

## Input
- `output/step04/structural_mask.npy`

## Required behavior
- treat wall, window, and door as structural boundaries,
- flood fill from image borders,
- label reachable empty space as exterior,
- label remaining enclosed empty space as interior.

## Final encoding for this step
- `0 = exterior`
- `1 = wall`
- `2 = window`
- `3 = door`
- `4 = interior`

## Outputs
- `output/step05/space_classified.npy`
- `output/step05/space_classified.png`
- `output/step05/space_overlay.png`
- `output/step05/regions_report.txt`

## Acceptance criteria
- enclosed spaces become interior,
- border-connected outside remains exterior,
- the classification is visually plausible.

## Suggested implementation notes
- Keep the flood fill logic easy to inspect.
- Report suspicious cases such as nearly everything becoming exterior.

## Manual test
1. Inspect `space_classified.png`.
2. Confirm the outside of the floorplan is exterior.
3. Confirm enclosed rooms look interior.
