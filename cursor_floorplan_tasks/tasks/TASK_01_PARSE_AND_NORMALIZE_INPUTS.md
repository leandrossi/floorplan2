# TASK 01 — Parse and Normalize Inputs

## Goal
Create a normalization layer for both Roboflow outputs so all downstream steps consume a stable schema.

## Target file
`src/step01_parse_and_normalize_inputs.py`

## Why this task exists
The project uses two separate model outputs:
- structural detections,
- room detections.

They must be normalized into a consistent format before any rasterization or topology work begins.

## Inputs
- `input/result_structure.json`
- `input/result_rooms.json`

## Required behavior
### Structural normalization
Map classes as follows:
- `Wall` → `wall`
- `Window` → `window`
- `Door` → `door`
- `diagonal` → `wall`

For each prediction preserve:
- normalized class,
- original class,
- confidence,
- polygon points,
- bbox,
- detection id,
- optional derived orientation metadata.

### Room normalization
Map:
- `room` → `room`

For each prediction preserve:
- confidence,
- polygon points,
- bbox,
- detection id.

### Validations
- confirm both runs share the same image size if available,
- detect missing polygon points,
- use bbox fallback only when polygon is missing,
- generate a readable summary.

## Outputs
- `output/step01/normalized_structure.json`
- `output/step01/normalized_rooms.json`
- `output/step01/summary.txt`

## Acceptance criteria
- `diagonal` is converted to `wall`,
- structure and rooms use a unified schema,
- no useful detections are silently dropped,
- summary shows counts by original and normalized class.

## Suggested implementation notes
- Keep normalization explicit and simple.
- Do not add heavy abstractions.
- Make the output schema easy to inspect in raw JSON.

## Manual test
1. Run the script.
2. Inspect `summary.txt`.
3. Confirm `diagonal` appears in original counts but is represented as `wall` in normalized counts.
4. Confirm room predictions are preserved.
