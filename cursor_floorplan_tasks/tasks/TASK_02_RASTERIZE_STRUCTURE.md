# TASK 02 — Rasterize Structure

## Goal
Convert normalized structural predictions into a pixel mask with deterministic class priority.

## Target file
`src/step02_rasterize_structure.py`

## Why this task exists
The downstream topology logic must operate on a dense structural mask, not raw polygons.

## Input
- `output/step01/normalized_structure.json`

## Required behavior
- Create an empty canvas at the original image size.
- Rasterize structure polygons.
- Use this draw priority:
  1. `wall`
  2. `window`
  3. `door`

## Intermediate encoding
- `0 = empty`
- `1 = wall`
- `2 = window`
- `3 = door`

## Outputs
- `output/step02/raw_structure_mask.npy`
- `output/step02/raw_structure_mask.png`
- `output/step02/raw_structure_overlay.png`

## Acceptance criteria
- diagonal walls are present in the wall layer,
- windows and doors visually align with the plan,
- priority overwriting works consistently.

## Suggested implementation notes
- Prefer polygon rasterization.
- If polygon points are missing, allow bbox fallback.
- Keep color mapping fixed in preview images.

## Manual test
1. Run the script.
2. Inspect `raw_structure_overlay.png`.
3. Confirm walls, windows, doors appear in sensible locations.
4. Confirm diagonal walls are visible as wall.
