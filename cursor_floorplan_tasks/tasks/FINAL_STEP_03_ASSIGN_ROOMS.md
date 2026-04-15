# Final Step 03 — Assign room ids

## Script
`src/final_step03_assign_rooms.py`

## Inputs
- `output/final/step02/space_classified.npy`
- `output/final/step01/room_polygons.npy`

## Outputs (`output/final/step03/`)
- `room_id_matrix.npy`
- `room_id_preview.png`, `rooms_report.txt`

## Responsibilities
- Build topological interior regions from classified space.
- Claim regions using room polygon overlap / confidence where applicable.

## Validation
- Distinct rooms get distinct ids; door choke points do not spuriously merge regions.
