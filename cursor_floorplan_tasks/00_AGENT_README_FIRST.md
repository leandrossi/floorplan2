# READ THIS FIRST — Cursor Agent Instructions

## Purpose
This folder contains the project context and the task breakdown for the **Floorplan to Matrix Pipeline** (final unified flow).

The goal is to let the Cursor agent read the files in order and execute the work with a clear understanding of:
- project objective,
- current decisions already taken,
- architecture boundaries,
- one-task-per-file implementation scope,
- outputs expected from every step,
- validation criteria,
- manual tests.

## Read order
Read the files in this exact order:

1. `00_AGENT_README_FIRST.md`
2. `01_PROJECT_CONTEXT.md`
3. `02_PIPELINE_OVERVIEW.md`
4. `03_DATA_CONTRACTS.md`
5. `04_TESTING_AND_DEBUG_RULES.md`
6. `tasks/FINAL_STEP_01_PARSE_RASTERIZE.md`
7. `tasks/FINAL_STEP_02_CLASSIFY_SPACE.md`
8. `tasks/FINAL_STEP_03_ASSIGN_ROOMS.md`
9. `tasks/FINAL_STEP_04_MATRIX_CSV.md`
10. `tasks/FINAL_STEP_05_PLAN_ALARM.md`

## Important decisions already closed
Do not reopen these decisions unless the user explicitly changes them.

1. **The structural model is the geometric source of truth.**
2. **The room model is an auxiliary source for room assignment/validation only.**
3. **`diagonal` must be treated as `wall`.**
4. **Doors must be treated as temporarily closed for room segmentation.**
5. **The system must generate two final matrices:**
   - structural matrix,
   - room-id matrix.
6. **Every step must produce a visible/debuggable output.**
7. **The implementation must be deterministic and easy to inspect.**

## What the agent should optimize for
- correctness over elegance,
- observability over compactness,
- simple deterministic code over heavy abstractions,
- step-by-step outputs that the user can evaluate visually.

## What not to do
- Do not collapse all logic into one file.
- Do not mix structural classes and room ids into a single final matrix at this stage.
- Do not treat the room model as the primary geometric truth.
- Do not discard diagonal walls.
- Do not assume real 5 cm scale unless scale data is explicitly available.

## Expected tech style
- Python
- Simple file-based pipeline
- Clear CLI entry point per step
- Numpy/OpenCV/Pillow style utilities are acceptable
- Prefer easy-to-debug procedural code
