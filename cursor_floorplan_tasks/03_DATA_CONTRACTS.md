# Data Contracts (final pipeline)

## Inputs
### Roboflow unified JSON
- **Path (default):** `output/result_workflow_final.json`
- **Produced by:** `run_workflow_final.py` or the wizard after image upload.
- **Shape:** Roboflow workflow with `runs[0].workflow_output[0]` containing:
  - `structural_predictions` (bbox-style wall/window/door),
  - `room_predictions` (polygon `room` detections),
  - embedded `image` width/height.

### Configuration
- **`config/pipeline_config.json`** — cell size, thresholds, planner-related settings loaded by final steps and step05.

## Output directory layout
Only **`output/final/`** and the **unified JSON** at `output/result_workflow_final.json` are part of the current contract. Legacy paths `output/step01` … `output/step09` are not used.

```text
output/
├─ result_workflow_final.json          # Roboflow unified result (regenerable)
└─ final/
   ├─ step01/
   ├─ step02/
   ├─ step03/
   ├─ step04/
   └─ step05/
```

## Step 01 (`output/final/step01/`)
- `structural_mask.npy`, `room_polygons.npy`
- `structural_mask.png`, `room_polygons.png`
- `parse_report.txt`, `parse_meta.json`

## Step 02 (`output/final/step02/`)
- `space_classified.npy` — full 0–4 space classification
- `space_classified.png`, `space_overlay.png`
- `classify_report.txt`

## Step 03 (`output/final/step03/`)
- `room_id_matrix.npy`
- `room_id_preview.png`
- `rooms_report.txt`

## Step 04 (`output/final/step04/`)
- `final_structure_matrix.npy`, `final_rooms_matrix.npy`, `final_rooms_inferred_mask.npy`
- `final_structure_matrix.csv`, `final_rooms_matrix.csv`
- `floor_like.csv`, `floor_like_tokens.npy` (optional downstream)
- Previews: `final_structure_preview.png`, `floor_like_preview.png`
- Human review: `review_bundle.json`; saved approvals: `review_approved.json`
- Reports: `infer_report.txt`, `opening_adjacency_report.txt`, etc.
- `final_metadata.json`

## Step 05 (`output/final/step05/`)
- `installation_proposal.json`, `alarm_plan_report.json`
- `final_floorplan_grid.json`, `final_structure_effective.npy`
- `devices_layer.csv`, `floor_like_with_devices.csv`
- Renders: `floorplan_clean.png`, `floorplan_devices.png`, `floorplan_ai_reference.png`

## Structural class encoding (final matrices)
- `0` exterior
- `1` wall
- `2` window
- `3` door
- `4` interior

## Room-id encoding
- `0` not-a-room / exterior / structure
- `1..N` room ids

## Intermediate mask (step01 structural raster)
- `0` free
- `1` wall
- `2` window
- `3` door

## Scale policy
If real-world scale is not available, metadata must state `relative_scale` (or equivalent) explicitly.
