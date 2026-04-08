# Pipeline Overview

## Final pipeline
The pipeline is split into 7 executable steps.

1. Parse and normalize both model outputs
2. Rasterize the structural detections
3. Repair wall topology
4. Build the consolidated structural mask
5. Classify exterior vs interior
6. Assign room ids using topological regions + room-model proposals
7. Build final exported outputs

## Why this split exists
This split is intentional.

The user wants:
- one file per stage,
- one visible output per stage,
- the ability to evaluate behavior during experimentation,
- no black-box monolith.

## High-level flow
```text
result_structure.json ─┐
                       ├─ step01 → normalized_structure.json
result_rooms.json ─────┘           normalized_rooms.json

normalized_structure.json → step02 → raw_structure_mask
raw_structure_mask       → step03 → repaired_wall_mask
raw_structure_mask + repaired_wall_mask → step04 → structural_mask
structural_mask          → step05 → space_classified
normalized_rooms.json + space_classified → step06 → room_id_matrix
space_classified + room_id_matrix → step07 → final exported matrices
```

## Key implementation principle
The room segmentation must be built on top of the structural topology, not the other way around.

That means:
- first understand where the structure closes,
- then identify interior regions,
- then map room-model predictions to those real regions.

## Output layers
### Layer 1 — Structure
- exterior
- wall
- window
- door
- interior

### Layer 2 — Room ids
- no-room / non-free-space
- room ids for free interior cells

Keep these layers separate.
