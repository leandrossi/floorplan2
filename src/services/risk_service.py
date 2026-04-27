from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from domain.contracts import RiskViewModel
from infrastructure.artifact_store import ArtifactStore
from infrastructure.review_bundle_adapter import ReviewBundleAdapter
from review_bundle_io import apply_struct_patches, load_approved
from ui.components.plan_canvas import overlay_marker_icons
from ui_components import alpha_blend, compute_pre_suppression_red_mask, rgb_from_struct, upscale_rgb

FIXED_RISK_LEVEL = "optimal"
RISK_RENDER_WIDTH = 1800
RISK_ICON_SIZE_PX = 20


def _expand_mask(mask: np.ndarray, radius: int) -> np.ndarray:
    if radius <= 0:
        return mask
    h, w = mask.shape
    out = mask.copy()
    for dr in range(-radius, radius + 1):
        for dc in range(-radius, radius + 1):
            if dr == 0 and dc == 0:
                continue
            shifted = np.zeros((h, w), dtype=bool)
            src_r0 = max(0, -dr)
            src_r1 = min(h, h - dr)
            src_c0 = max(0, -dc)
            src_c1 = min(w, w - dc)
            dst_r0 = max(0, dr)
            dst_r1 = min(h, h + dr)
            dst_c0 = max(0, dc)
            dst_c1 = min(w, w + dc)
            shifted[dst_r0:dst_r1, dst_c0:dst_c1] = mask[src_r0:src_r1, src_c0:src_c1]
            out |= shifted
    return out


def _upscale_mask(mask: np.ndarray, target_w: int) -> np.ndarray:
    h, w = mask.shape
    if w <= 0 or h <= 0 or target_w <= w:
        return mask
    target_h = max(1, round(h * target_w / w))
    pil = Image.fromarray(mask.astype(np.uint8) * 255).resize((target_w, target_h), Image.NEAREST)
    return np.asarray(pil) > 0


class RiskService:
    def __init__(
        self,
        adapter: ReviewBundleAdapter | None = None,
        artifact_store: ArtifactStore | None = None,
    ) -> None:
        self.adapter = adapter or ReviewBundleAdapter()
        self.artifact_store = artifact_store or ArtifactStore()

    def build(
        self,
        *,
        review_bundle_path: Path,
        review_approved_path: Path,
        output_path: Path,
    ) -> RiskViewModel:
        bundle = self.adapter.load(review_bundle_path)
        approved = load_approved(review_approved_path)
        if approved is None:
            raise RuntimeError("Approved review is required to build the diagnosis.")

        effective_struct = apply_struct_patches(bundle.struct, approved.get("struct_patch") or [])
        main_entry = approved.get("main_entry")
        electric_board = approved.get("electric_board")

        base_rgb_native = rgb_from_struct(effective_struct)
        base_rgb = upscale_rgb(base_rgb_native, RISK_RENDER_WIDTH)
        base_rgb = overlay_marker_icons(
            base_rgb,
            grid_h=effective_struct.shape[0],
            grid_w=effective_struct.shape[1],
            main_entry=main_entry,
            electric_board=electric_board,
            icon_size_px=RISK_ICON_SIZE_PX,
        )
        base_plan_path = self.artifact_store.write_rgb_image(output_path.parent / "risk_base_plan.png", base_rgb)

        red_mask = compute_pre_suppression_red_mask(
            effective_struct,
            main_entry=main_entry,
            electric_board=electric_board,
            cell_size_m=bundle.cell_size_m,
            security_level=FIXED_RISK_LEVEL,
        )
        risk_rgb = base_rgb.copy()
        red_cells = 0
        if isinstance(red_mask, np.ndarray):
            red_cells = int(red_mask.sum())
            if red_cells > 0:
                red_mask_up = _upscale_mask(red_mask, RISK_RENDER_WIDTH)
                medium_mask = _expand_mask(red_mask_up, radius=16) & ~red_mask_up
                risk_rgb = alpha_blend(risk_rgb, medium_mask, (247, 179, 194), alpha=0.34)
                risk_rgb = alpha_blend(risk_rgb, red_mask_up, (232, 93, 117), alpha=0.55)
                risk_rgb = overlay_marker_icons(
                    risk_rgb,
                    grid_h=effective_struct.shape[0],
                    grid_w=effective_struct.shape[1],
                    main_entry=main_entry,
                    electric_board=electric_board,
                    icon_size_px=RISK_ICON_SIZE_PX,
                )
        risk_overlay_path = self.artifact_store.write_rgb_image(output_path, risk_rgb)

        if red_cells > 0:
            summary = (
                "We identified the most exposed areas based on access routes and circulation inside the home. "
                "This baseline diagnosis is set—next, we'll show you different ways to cover these zones."
            )
            details = [
                "Most exposed zones detected.",
                "Main entrance included in the analysis.",
                "Diagnosis ready for coverage planning.",
            ]
        else:
            summary = (
                "We didn't find persistent high-exposure zones in this baseline view. "
                "We'll still show you a recommended solution for access and circulation."
            )
            details = [
                "No persistent critical zones detected.",
                "Main entrance included in the analysis.",
                "Diagnosis ready for coverage planning.",
            ]

        return RiskViewModel(
            base_plan_path=str(base_plan_path),
            risk_overlay_path=str(risk_overlay_path),
            legend=[
                {"label": "Baseline diagnosis", "color": "Translucent red"},
                {"label": "Main entrance", "color": "Solid red"},
                {"label": "Electrical board", "color": "Solid blue"},
            ],
            summary_text=summary,
            details=details,
        )
