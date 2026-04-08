# Project Context

## Project name
Floorplan to Matrix Pipeline

## Core objective
Convert a floorplan image into two machine-usable matrix outputs.

### Output A — Structural matrix
Cell meaning:
- `0 = exterior`
- `1 = wall`
- `2 = window`
- `3 = door`
- `4 = interior`

### Output B — Room-id matrix
Cell meaning:
- `0 = not-a-room / exterior / structure`
- `1..N = room_id`

## What the project is solving
The project needs to take a floorplan and turn it into a discrete grid that can later be consumed by other logic.

The immediate scope is:
1. detect walls, windows, doors,
2. build a structural mask,
3. separate exterior from interior,
4. identify real interior regions,
5. assign each region a room id,
6. export matrices for downstream use.

## What is NOT in scope right now
- OCR of room labels,
- semantic room naming (`kitchen`, `bathroom`, etc.),
- full CAD reconstruction,
- perfect architectural vectorization,
- production optimization.

## Current data sources
There are two Roboflow runs for the same floorplan.

### 1. Structural run
Contains detections such as:
- `Wall`
- `Window`
- `Door`
- `diagonal`

### 2. Room run
Contains detections such as:
- `room`

## Closed interpretation rules
### Structural source of truth
The structural run is the primary geometric truth for:
- walls,
- windows,
- doors,
- layout boundaries.

### Room run usage
The room run is used only to:
- propose room regions,
- help assign room ids,
- validate interior segmentation.

It must not replace the topological segmentation derived from the structural layout.

### Diagonal class
`diagonal` must be treated as `wall`.
It represents a wall drawn diagonally instead of horizontally/vertically.

### Doors for room segmentation
When segmenting rooms, doors must be treated as temporarily closed. Otherwise adjacent rooms connected by a door may collapse into one region.

## Main engineering philosophy
- one file per step,
- visible output per step,
- deterministic behavior,
- easy manual validation,
- easy debugging.

## Success criteria for this stage
This stage is successful if:
- the structural matrix is coherent,
- diagonal walls are preserved as walls,
- exterior/interior are separated correctly,
- room ids are assigned consistently,
- every step can be inspected visually.
