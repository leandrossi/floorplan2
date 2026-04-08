#!/usr/bin/env python3
"""
Workflow final unificado:
floorplan-final-analysis-1775593034044
"""
from __future__ import annotations

from roboflow_workflow_common import DEFAULT_OUTPUT_DIR, WorkflowScriptConfig, main_entry

CONFIG = WorkflowScriptConfig(
    workflow_id="floorplan-final-analysis-1775593034044",
    description="Roboflow: floorplan-final-analysis-1775593034044",
    default_json_name="result_workflow_final.json",
    default_vis_suffix="_roboflow_vis_final",
    default_output_dir=DEFAULT_OUTPUT_DIR,
)


if __name__ == "__main__":
    main_entry(CONFIG)
