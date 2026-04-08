#!/usr/bin/env python3
"""
Ejemplo: Floorplan2.png → workflow 1 (detect-count-and-visualize) → workflow 2.

Llama a main_entry en el mismo proceso (no subprocess) para que el cwd no rompa
load_dotenv ni el layout de imports.
"""
from __future__ import annotations

import sys
from pathlib import Path

from roboflow_workflow_common import PROJECT_ROOT, main_entry
from run_mvp import CONFIG as CONFIG_WF1
from run_workflow2 import CONFIG as CONFIG_WF2


def main() -> None:
    img = PROJECT_ROOT / "Floorplan2.png"
    if not img.is_file():
        print(f"Falta imagen de ejemplo: {img}", file=sys.stderr)
        sys.exit(1)

    argv = [str(img)]

    print("\n--- workflow 1 (detect-count-and-visualize) ---", file=sys.stderr)
    main_entry(CONFIG_WF1, argv=argv)

    print("\n--- workflow 2 (detect-count-and-visualize-2) ---", file=sys.stderr)
    main_entry(CONFIG_WF2, argv=argv)

    print(
        "\nPipeline OK: output/result.json y output/result_workflow2.json",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
