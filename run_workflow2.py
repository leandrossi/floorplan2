#!/usr/bin/env python3
"""
Workflow 2: detect-count-and-visualize-2
"""
from __future__ import annotations

from roboflow_workflow_common import DEFAULT_OUTPUT_DIR, WorkflowScriptConfig, main_entry

CONFIG = WorkflowScriptConfig(
    workflow_id="detect-count-and-visualize-2",
    description="Roboflow: detect-count-and-visualize-2",
    default_json_name="result_workflow2.json",
    default_vis_suffix="_roboflow_vis2",
    default_output_dir=DEFAULT_OUTPUT_DIR,
)


if __name__ == "__main__":
    main_entry(CONFIG)
