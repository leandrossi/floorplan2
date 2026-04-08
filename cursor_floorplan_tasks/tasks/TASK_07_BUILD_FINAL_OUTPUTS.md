# TASK 07 — Build Final Outputs

## Goal
Export the final structural and room-id matrices plus metadata and previews.

## Target file
`src/step07_build_final_outputs.py`

## Why this task exists
The project needs standardized final outputs that downstream logic can consume.

## Inputs
- `output/step05/space_classified.npy`
- `output/step06/room_id_matrix.npy`
- `config/pipeline_config.json`

## Required behavior
### Structural matrix
Export final structure using:
- `0 = exterior`
- `1 = wall`
- `2 = window`
- `3 = door`
- `4 = interior`

### Room matrix
Export final room ids using:
- `0 = not-a-room / exterior / structure`
- `1..N = room ids`

### Scale behavior
- if real scale info exists, convert to the requested cell size,
- if it does not exist, work in relative scale mode and record that clearly.

## Outputs
- `output/step07/final_structure_matrix.npy`
- `output/step07/final_structure_matrix.csv`
- `output/step07/final_rooms_matrix.npy`
- `output/step07/final_rooms_matrix.csv`
- `output/step07/final_structure_preview.png`
- `output/step07/final_rooms_preview.png`
- `output/step07/final_metadata.json`

## Acceptance criteria
- two final matrix layers are exported,
- previews are readable,
- metadata clearly states whether scale is real or relative,
- exported files are consistent with intermediate outputs.

## Suggested implementation notes
- Keep export functions simple and deterministic.
- Do not merge structure and room ids into one matrix in this stage.

## Manual test
1. Open final previews.
2. Inspect final CSV outputs.
3. Confirm metadata contains scale mode and class conventions.
