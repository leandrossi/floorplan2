#!/usr/bin/env python3
"""
Workflow 1: detect-count-and-visualize
"""
from __future__ import annotations

from roboflow_workflow_common import DEFAULT_OUTPUT_DIR, WorkflowScriptConfig, main_entry

CONFIG = WorkflowScriptConfig(
    workflow_id="detect-count-and-visualize",
    description="Roboflow: detect-count-and-visualize",
    default_json_name="result.json",
    default_vis_suffix="_roboflow_vis",
    default_output_dir=DEFAULT_OUTPUT_DIR,
)


if __name__ == "__main__":
    main_entry(CONFIG)
