# Final Step 04 — Build final matrices and CSVs

## Script
`src/final_step04_build_matrix_csv.py`

## Inputs
- `output/final/step02/space_classified.npy`
- `output/final/step03/room_id_matrix.npy`
- `config/pipeline_config.json`

## Outputs (`output/final/step04/`)
- `final_structure_matrix.npy`, `final_rooms_matrix.npy`, `final_rooms_inferred_mask.npy`
- CSV exports, token grid if enabled, PNG previews
- `review_bundle.json` for Streamlit wizard
- Reports (`infer_report.txt`, `opening_adjacency_report.txt`, …)

## Responsibilities
- Produce the canonical 0–4 structural grid and room-id grid for review and step05.
- Seal micro-gaps / opening rules as implemented in code.

## Validation
- Previews match intuition; `review_bundle.json` round-trips in the wizard.
