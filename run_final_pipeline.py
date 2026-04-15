#!/usr/bin/env python3
"""Orchestrator for the final unified pipeline (steps 01–05).

After step04, optional human review in the wizard (save review_approved.json):
  PYTHONPATH=src streamlit run src/wizard_app.py
Then re-run step05 (or let this script continue; it uses review_approved.json if saved).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
STEPS = [
    "final_step01_parse_and_rasterize.py",
    "final_step02_classify_space.py",
    "final_step03_assign_rooms.py",
    "final_step04_build_matrix_csv.py",
    "final_step05_plan_alarm.py",
]


def main() -> None:
    for s in STEPS:
        script = SRC / s
        print(f"\n>>> {s}", flush=True)
        r = subprocess.run([sys.executable, str(script)], check=False)
        if r.returncode != 0:
            print(f"Fallo en {s} (exit {r.returncode})", file=sys.stderr)
            sys.exit(r.returncode)
        if s == "final_step04_build_matrix_csv.py" and r.returncode == 0:
            root = Path(__file__).resolve().parent
            print(
                "\n--- Optional review (save review_approved.json in step04 for step05) ---\n"
                f"  cd {root} && PYTHONPATH=src streamlit run src/wizard_app.py\n",
                flush=True,
            )
    print("\nFinal pipeline OK -> output/final/step01 … step05", flush=True)


if __name__ == "__main__":
    main()
