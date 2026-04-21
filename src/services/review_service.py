from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from domain.contracts import ReviewResult
from grid_topology_validate import (
    build_validation_checklist,
    collect_validation_highlight_cells,
    validate_grid_for_alarm,
)
from infrastructure.artifact_store import ArtifactStore
from infrastructure.review_bundle_adapter import ReviewBundleAdapter, ReviewBundleData
from review_bundle_io import apply_struct_patches
from ui_components import overlay_markers, rgb_from_struct


class ReviewService:
    def __init__(
        self,
        adapter: ReviewBundleAdapter | None = None,
        artifact_store: ArtifactStore | None = None,
    ) -> None:
        self.adapter = adapter or ReviewBundleAdapter()
        self.artifact_store = artifact_store or ArtifactStore()

    def load_bundle(self, bundle_path: Path) -> ReviewBundleData:
        return self.adapter.load(bundle_path)

    def build_approved_payload(
        self,
        *,
        bundle: ReviewBundleData,
        struct_patch: list[dict[str, int]],
        main_entry: list[int] | None,
        electric_board: list[int] | None,
    ) -> dict[str, Any]:
        return {
            "version": 1,
            "main_entry": main_entry,
            "electric_board": electric_board,
            "struct_patch": struct_patch,
            "source_bundle": str(bundle.bundle_path),
            "approved_at": datetime.now(timezone.utc).isoformat(),
        }

    def effective_struct(
        self,
        bundle: ReviewBundleData,
        struct_patch: list[dict[str, int]],
    ) -> np.ndarray:
        return apply_struct_patches(bundle.struct, struct_patch)

    def build_validation_state(
        self,
        *,
        bundle_path: Path,
        struct_patch: list[dict[str, int]],
        main_entry: list[int] | None,
        electric_board: list[int] | None,
    ) -> dict[str, Any]:
        bundle = self.load_bundle(bundle_path)
        approved = self.build_approved_payload(
            bundle=bundle,
            struct_patch=struct_patch,
            main_entry=main_entry,
            electric_board=electric_board,
        )
        effective_struct = self.effective_struct(bundle, struct_patch)
        checklist = build_validation_checklist(
            effective_struct,
            approved,
            require_markers=True,
            main_entry_must_touch_exterior=True,
        )
        error_cells, warning_short, warning_long = collect_validation_highlight_cells(
            effective_struct,
            approved,
            require_markers=True,
            main_entry_must_touch_exterior=True,
        )
        blocking_errors, warnings = validate_grid_for_alarm(
            effective_struct,
            approved,
            require_markers=True,
            main_entry_must_touch_exterior=True,
        )
        return {
            "bundle": bundle,
            "effective_struct": effective_struct,
            "approved": approved,
            "checklist": checklist,
            "error_cells": error_cells,
            "warning_short_cells": warning_short,
            "warning_long_cells": warning_long,
            "blocking_errors": blocking_errors,
            "warnings": warnings,
        }

    def approve(
        self,
        *,
        bundle_path: Path,
        review_dir: Path,
        struct_patch: list[dict[str, int]],
        main_entry: list[int] | None,
        electric_board: list[int] | None,
    ) -> ReviewResult:
        validation = self.build_validation_state(
            bundle_path=bundle_path,
            struct_patch=struct_patch,
            main_entry=main_entry,
            electric_board=electric_board,
        )
        bundle: ReviewBundleData = validation["bundle"]
        if validation["blocking_errors"]:
            return ReviewResult(
                approved=False,
                review_bundle_path=str(bundle_path),
                review_approved_path=None,
                main_entry=main_entry,
                electric_board=electric_board,
                corrected_preview_path=None,
                blocking_errors=validation["blocking_errors"],
                warnings=validation["warnings"],
                checklist=[
                    {
                        "id": item.id,
                        "label": item.label,
                        "ok": item.ok,
                        "blocks_proposal": item.blocks_proposal,
                        "detail": item.detail,
                    }
                    for item in validation["checklist"]
                ],
            )

        effective_struct = validation["effective_struct"]
        approved_payload = validation["approved"]
        approved_path = self.artifact_store.write_json(review_dir / "review_approved.json", approved_payload)
        corrected_rgb = overlay_markers(
            rgb_from_struct(effective_struct),
            main_entry=main_entry,
            electric_board=electric_board,
            marker_radius=2,
        )
        corrected_preview_path = self.artifact_store.write_rgb_image(
            review_dir / "corrected_plan.png",
            corrected_rgb,
        )
        self.artifact_store.copy_if_exists(bundle.bundle_path, review_dir / "review_bundle.json")
        return ReviewResult(
            approved=True,
            review_bundle_path=str(bundle_path),
            review_approved_path=str(approved_path),
            main_entry=main_entry,
            electric_board=electric_board,
            corrected_preview_path=str(corrected_preview_path),
            blocking_errors=[],
            warnings=validation["warnings"],
            checklist=[
                {
                    "id": item.id,
                    "label": item.label,
                    "ok": item.ok,
                    "blocks_proposal": item.blocks_proposal,
                    "detail": item.detail,
                }
                for item in validation["checklist"]
            ],
        )
