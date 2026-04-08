# Data Contracts

## Input directory
```text
input/
├─ Floorplan2.png
├─ result_structure.json
└─ result_rooms.json
```

## Output directory
```text
output/
├─ step01/
├─ step02/
├─ step03/
├─ step04/
├─ step05/
├─ step06/
└─ step07/
```

## Step 01 outputs
- `normalized_structure.json`
- `normalized_rooms.json`
- `summary.txt`

## Step 02 outputs
- `raw_structure_mask.npy`
- `raw_structure_mask.png`
- `raw_structure_overlay.png`

## Step 03 outputs
- `repaired_wall_mask.npy`
- `repaired_wall_mask.png`
- `wall_diff.png`
- `wall_repair_report.txt`

## Step 04 outputs
- `structural_mask.npy`
- `structural_mask.png`
- `structural_overlay.png`
- `structural_conflicts_report.txt`

## Step 05 outputs
- `space_classified.npy`
- `space_classified.png`
- `space_overlay.png`
- `regions_report.txt`

## Step 06 outputs
- `room_id_matrix.npy`
- `room_id_matrix.csv`
- `room_id_preview.png`
- `rooms_match_report.txt`

## Step 07 outputs
- `final_structure_matrix.npy`
- `final_structure_matrix.csv`
- `final_rooms_matrix.npy`
- `final_rooms_matrix.csv`
- `final_structure_preview.png`
- `final_rooms_preview.png`
- `final_metadata.json`

## Structural class encoding
Use this encoding consistently once the structural mask is consolidated:
- `0 = exterior`
- `1 = wall`
- `2 = window`
- `3 = door`
- `4 = interior`

## Room-id encoding
Use this encoding consistently for room labels:
- `0 = not-a-room / exterior / structure`
- `1..N = room ids`

## Mask conventions during intermediate steps
### Step 02 and Step 04 structural raster masks
- `0 = empty`
- `1 = wall`
- `2 = window`
- `3 = door`

### Step 05 classified space
- `0 = exterior`
- `1 = wall`
- `2 = window`
- `3 = door`
- `4 = interior`

## Fallback policy
If a prediction lacks polygon points but has a valid bbox, bbox may be used as fallback in Step 01 normalization.

## Scale policy
If real-world scale is not available, the pipeline must work in `relative_scale` mode and state that clearly in metadata.
