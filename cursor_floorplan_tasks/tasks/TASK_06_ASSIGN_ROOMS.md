# TASK 06 — Assign Rooms

## Goal
Assign room ids to interior regions by combining topological segmentation with the room-model predictions.

## Target file
`src/step06_assign_rooms.py`

## Why this task exists
The room-model output contains room proposals, but the project must derive stable room ids from the structural topology.

## Inputs
- `output/step01/normalized_rooms.json`
- `output/step05/space_classified.npy`

## Required behavior
### A. Rasterize room proposals
Rasterize each normalized `room` polygon into a room-candidate layer.

### B. Temporarily close doors
Create a temporary version of the structural classification where doors behave like barriers. This prevents adjacent rooms connected by a door from collapsing into one interior region.

### C. Compute real interior regions
Run connected-component labeling on the interior free space.

### D. Match room proposals to real interior regions
Rules:
- if a topological region overlaps strongly with one room proposal, assign that room id,
- if multiple room proposals overlap one region, choose the best overlap/confidence combination,
- if one room proposal spans multiple structural regions, split by topology,
- if a structural interior region has no room proposal, still assign a new room id.

## Room-id encoding
- `0 = not-a-room / exterior / structure`
- `1..N = room ids`

## Outputs
- `output/step06/room_id_matrix.npy`
- `output/step06/room_id_matrix.csv`
- `output/step06/room_id_preview.png`
- `output/step06/rooms_match_report.txt`

## Acceptance criteria
- each real interior region receives a stable room id,
- doors do not cause adjacent rooms to merge,
- room-model predictions improve labeling rather than overriding topology.

## Suggested implementation notes
- Keep overlap metrics explicit.
- Save enough info in the report so matching decisions can be understood.
- Deterministic room-id assignment is important.

## Manual test
1. Inspect room preview.
2. Confirm distinct enclosed regions have different ids.
3. Confirm the room-model proposals align reasonably with topological regions.
