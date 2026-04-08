"""
Test configuration: ensure the src/ directory is on sys.path so that
`import acala_engine` works when running pytest from the project root.
"""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
