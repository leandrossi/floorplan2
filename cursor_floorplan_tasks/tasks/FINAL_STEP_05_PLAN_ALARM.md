# Final Step 05 — Alarm planning

## Script
`src/final_step05_plan_alarm.py`

## Inputs
- `output/final/step04/` matrices and optional `floor_like_tokens.npy`
- `output/final/step04/review_approved.json` if present (main entry, electric board, struct patches, security level)
- `config/pipeline_config.json`

## Outputs (`output/final/step05/`)
- `installation_proposal.json`, `alarm_plan_report.json`
- `final_floorplan_grid.json`, `final_structure_effective.npy`
- `devices_layer.csv`, `floor_like_with_devices.csv`
- Proposal visualization PNGs

## Responsibilities
- Build `acala_engine` scenario from grids + approved human markers.
- Run deterministic planner; write machine- and human-readable exports.

## Validation
- Engine completes; proposal JSON schema matches consumer expectations.
- Re-run is deterministic for same inputs.
