# Final Step 01 — Parse unified JSON and rasterize

## Script
`src/final_step01_parse_and_rasterize.py`

## Inputs
- `output/result_workflow_final.json` (or path via CLI)

## Outputs (`output/final/step01/`)
- `structural_mask.npy`, `room_polygons.npy`
- PNG previews, `parse_report.txt`, `parse_meta.json`

## Responsibilities
- Read Roboflow unified block (`runs[0].workflow_output[0]`).
- Rasterize structural classes as bbox-filled rects (walls → windows/doors paint order).
- Rasterize room polygons with confidence ordering for overlap.

## Validation
- Image dimensions consistent between structural and room blocks.
- Non-empty structural mask for real floorplans.
