# Final Step 02 — Classify space

## Script
`src/final_step02_classify_space.py`

## Inputs
- `output/final/step01/structural_mask.npy`
- `output/final/step01/room_polygons.npy`

## Outputs (`output/final/step02/`)
- `space_classified.npy` (encoding 0–4 aligned with final struct matrix)
- Preview PNGs, `classify_report.txt`

## Responsibilities
- Flood-fill / topology from structural walls to separate exterior vs interior.
- Classify openings and interior free space consistently with downstream step03/04.

## Validation
- Preview: building interior reads as interior; yard reads as exterior.
