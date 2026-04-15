"""Tests for exterior border padding (openings + walls, single union pad)."""
from __future__ import annotations

import os
import sys
import unittest

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from struct_border_exterior_pad import (  # noqa: E402
    apply_struct_exterior_padding,
    compute_exterior_border_padding,
    pad_struct_grids_in_place,
)


class TestOpeningBorderPad(unittest.TestCase):
    def test_horizontal_opening_top_row_requests_top_pad(self) -> None:
        # 1×3 window on row 0 → long faces above/below; above is OOB
        s = np.array(
            [
                [1, 2, 2, 2, 1],
                [1, 4, 4, 4, 1],
            ],
            dtype=np.uint8,
        )
        pt, pb, pl, pr = compute_exterior_border_padding(s)
        self.assertGreaterEqual(pt, 1)
        # Walls on the sides may also request horizontal padding; opening still forces top.
        self.assertGreaterEqual(pt + pb + pl + pr, 1)

    def test_vertical_opening_left_col_requests_left_pad(self) -> None:
        s = np.array(
            [
                [1, 1, 4],
                [2, 1, 4],
                [2, 1, 4],
                [1, 1, 4],
            ],
            dtype=np.uint8,
        )
        pt, pb, pl, pr = compute_exterior_border_padding(s)
        self.assertGreaterEqual(pl, 1)


class TestWallBorderPad(unittest.TestCase):
    def test_horizontal_wall_along_top_edge(self) -> None:
        s = np.array(
            [
                [1, 1, 1, 1],
                [4, 4, 4, 4],
            ],
            dtype=np.uint8,
        )
        pt, _, _, _ = compute_exterior_border_padding(s)
        self.assertGreaterEqual(pt, 1)


class TestUnionNoDoubleColumn(unittest.TestCase):
    def test_opening_and_wall_same_edge_single_pad(self) -> None:
        s = np.array(
            [
                [1, 2, 2, 1],
                [1, 4, 4, 1],
            ],
            dtype=np.uint8,
        )
        pt, pb, pl, pr = compute_exterior_border_padding(s)
        self.assertEqual(pt, 1)
        self.assertEqual(pb, 0)


class TestApplyAndMultiPass(unittest.TestCase):
    def test_pad_then_stable(self) -> None:
        s = np.array(
            [
                [2, 2],
                [4, 4],
            ],
            dtype=np.uint8,
        )
        r = np.zeros_like(s, dtype=np.int32)
        f = np.zeros_like(s, dtype=np.uint8)
        sp, rp, fp, cum, logs = pad_struct_grids_in_place(s, r, f, max_passes=4)
        self.assertGreater(sp.shape[0], s.shape[0])
        self.assertTrue(logs)
        pt2, _, _, _ = compute_exterior_border_padding(sp)
        self.assertEqual(pt2, 0)

    def test_apply_padding_zeros(self) -> None:
        s = np.ones((2, 2), dtype=np.uint8)
        r = np.ones((2, 2), dtype=np.int32)
        f = np.ones((2, 2), dtype=np.uint8)
        sp, rp, fp = apply_struct_exterior_padding(s, r, f, (1, 0, 1, 0))
        self.assertEqual(sp.shape, (3, 3))
        self.assertTrue(np.all(sp[0, :] == 0))
        self.assertTrue(np.all(sp[:, 0] == 0))


if __name__ == "__main__":
    unittest.main()
