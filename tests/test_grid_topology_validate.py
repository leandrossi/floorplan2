"""Unit tests for grid topology validation (no Roboflow / Streamlit)."""
from __future__ import annotations

import os
import sys
import unittest

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from grid_topology_validate import (  # noqa: E402
    TopologyOptions,
    validate_grid_for_alarm,
    validate_topology,
)


class TestR1InteriorExterior(unittest.TestCase):
    def test_adjacent_4_0_fails(self) -> None:
        s = np.array(
            [
                [0, 0, 0],
                [0, 4, 0],
                [0, 0, 0],
            ],
            dtype=np.uint8,
        )
        r = validate_topology(s)
        codes = {e.code for e in r.errors}
        self.assertIn("INT_EXT_ADJ", codes)

    def test_separated_by_wall_ok(self) -> None:
        s = np.array(
            [
                [0, 0, 0, 0],
                [0, 1, 1, 1],
                [0, 1, 4, 1],
                [0, 1, 1, 1],
                [0, 0, 0, 0],
            ],
            dtype=np.uint8,
        )
        r = validate_topology(s)
        self.assertFalse(any(e.code == "INT_EXT_ADJ" for e in r.errors))


class TestR3ExteriorIsland(unittest.TestCase):
    def test_interior_hole_exterior(self) -> None:
        # Ring of walls around exterior pocket (0) not touching border
        s = np.array(
            [
                [1, 1, 1, 1, 1],
                [1, 4, 4, 4, 1],
                [1, 4, 0, 4, 1],
                [1, 4, 4, 4, 1],
                [1, 1, 1, 1, 1],
            ],
            dtype=np.uint8,
        )
        r = validate_topology(s)
        self.assertTrue(any(e.code == "EXTERIOR_ISLAND" for e in r.errors))


class TestOpeningAdjacencyWarning(unittest.TestCase):
    def test_long_side_wall_is_warning_not_error(self) -> None:
        # Horizontal 3×1 window; wall on top long side (row above bbox)
        s = np.ones((4, 5), dtype=np.uint8)
        s[0, :] = 0
        s[2, 1:4] = 2
        s[3, :] = 0
        r = validate_topology(s)
        self.assertTrue(any(e.code == "OPENING_LONG_SIDE_WALL" for e in r.warnings))
        self.assertFalse(any(e.code == "OPENING_LONG_SIDE_WALL" for e in r.errors))


class TestOpeningOrphan(unittest.TestCase):
    def test_window_surrounded_by_walls(self) -> None:
        s = np.array(
            [
                [1, 1, 1],
                [1, 2, 1],
                [1, 1, 1],
            ],
            dtype=np.uint8,
        )
        r = validate_topology(s)
        self.assertTrue(any(e.code == "OPENING_NO_ADJACENT_FREE" for e in r.errors))


class TestR4Optional(unittest.TestCase):
    def test_r4_off_by_default(self) -> None:
        s = np.ones((5, 5), dtype=np.uint8)
        s[2, 2] = 4
        r = validate_topology(s)
        self.assertFalse(any(e.code == "INTERIOR_LEAKS_TO_BORDER" for e in r.errors))

    def test_r4_on_flags_interior_reachable(self) -> None:
        # No walls — entire grid reachable from border
        s = np.array(
            [
                [4, 4, 4],
                [4, 4, 4],
                [4, 4, 4],
            ],
            dtype=np.uint8,
        )
        r = validate_topology(s, options=TopologyOptions(r4_interior_reachable_without_wall=True))
        self.assertTrue(any(e.code == "INTERIOR_LEAKS_TO_BORDER" for e in r.errors))


class TestValidateGridForAlarm(unittest.TestCase):
    def test_main_entry_must_touch_exterior(self) -> None:
        s = np.ones((5, 5), dtype=np.uint8)
        s[1:4, 1:4] = 4
        s[2, 2] = 3
        approved = {
            "version": 1,
            "main_entry": [2, 2],
            "electric_board": [1, 1],
            "struct_patch": [],
        }
        err, _ = validate_grid_for_alarm(s, approved, require_markers=True, main_entry_must_touch_exterior=True)
        self.assertTrue(any("MAIN_ENTRY_NO_EXTERIOR" in e for e in err))


if __name__ == "__main__":
    unittest.main()
