from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from domain.contracts import ProposalViewModel
from domain.enums import SecurityLevel
from infrastructure.alarm_engine_adapter import AlarmEngineAdapter
from infrastructure.artifact_store import ArtifactStore
from infrastructure.review_bundle_adapter import ReviewBundleAdapter
from review_bundle_io import apply_struct_patches, load_approved
from ui_components import overlay_device_icons, overlay_marker_icons, rgb_from_struct, upscale_rgb

ProgressCallback = Callable[[float, str], None]
PROPOSAL_RENDER_WIDTH = 1800
PROPOSAL_MAP_ICON_SIZE_PX = 24


def _neighbors4(r: int, c: int, h: int, w: int) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w:
            out.append((nr, nc))
    return out


def _find_keyboard_target_cell(
    struct,
    *,
    main_entry: list[int],
    blocked_cells: set[tuple[int, int]],
) -> tuple[int, int] | None:
    h, w = struct.shape
    door_r, door_c = int(main_entry[0]), int(main_entry[1])
    interior_neighbors = [
        (r, c)
        for (r, c) in _neighbors4(door_r, door_c, h, w)
        if int(struct[r, c]) == 4
    ]
    if not interior_neighbors:
        return None

    wall_candidates: list[tuple[int, int]] = []
    for ir, ic in interior_neighbors:
        for wr, wc in _neighbors4(ir, ic, h, w):
            if int(struct[wr, wc]) == 1 and (wr, wc) not in blocked_cells:
                wall_candidates.append((wr, wc))
    if wall_candidates:
        wall_candidates = sorted(
            set(wall_candidates),
            key=lambda cell: (abs(cell[0] - door_r) + abs(cell[1] - door_c), cell[0], cell[1]),
        )
        return wall_candidates[0]

    for ir, ic in interior_neighbors:
        if (ir, ic) not in blocked_cells:
            return (ir, ic)
    return None


class ProposalService:
    def __init__(
        self,
        adapter: AlarmEngineAdapter | None = None,
        review_adapter: ReviewBundleAdapter | None = None,
        artifact_store: ArtifactStore | None = None,
    ) -> None:
        self.adapter = adapter or AlarmEngineAdapter()
        self.review_adapter = review_adapter or ReviewBundleAdapter()
        self.artifact_store = artifact_store or ArtifactStore()

    def resolve_devices_for_overlay(
        self,
        *,
        review_bundle_path: Path,
        review_approved_path: Path,
        proposal_devices: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], int, int]:
        """Align proposal device cells with approved markers (same logic as overlay render)."""
        bundle = self.review_adapter.load(review_bundle_path)
        approved = load_approved(review_approved_path) or {}
        effective_struct = apply_struct_patches(bundle.struct, approved.get("struct_patch") or [])
        grid_h, grid_w = int(effective_struct.shape[0]), int(effective_struct.shape[1])

        devices = [dict(d) for d in proposal_devices if isinstance(d, dict)]
        main_entry = approved.get("main_entry")
        electric_board = approved.get("electric_board")
        if isinstance(main_entry, list) and len(main_entry) == 2:
            magnetic_idx = next(
                (idx for idx, d in enumerate(devices) if str(d.get("device_type") or "").lower() == "magnetic"),
                None,
            )
            keyboard_idx = next(
                (idx for idx, d in enumerate(devices) if str(d.get("device_type") or "").lower() == "keyboard"),
                None,
            )
            if magnetic_idx is not None:
                devices[magnetic_idx]["cell"] = [int(main_entry[0]), int(main_entry[1])]
            if keyboard_idx is not None:
                blocked_cells: set[tuple[int, int]] = {
                    (int(d["cell"][0]), int(d["cell"][1]))
                    for i, d in enumerate(devices)
                    if i != keyboard_idx
                    and isinstance(d.get("cell"), (list, tuple))
                    and len(d["cell"]) == 2
                }
                keyboard_target = _find_keyboard_target_cell(
                    effective_struct,
                    main_entry=main_entry,
                    blocked_cells=blocked_cells,
                )
                if keyboard_target is not None:
                    devices[keyboard_idx]["cell"] = [int(keyboard_target[0]), int(keyboard_target[1])]

        return devices, grid_h, grid_w

    def build(
        self,
        *,
        workspace,
        review_bundle_path: Path,
        review_approved_path: Path,
        level: SecurityLevel,
        progress_cb: ProgressCallback | None = None,
    ) -> ProposalViewModel:
        generated = self.adapter.generate_proposal(
            workspace,
            security_level=level.planner_code,
            review_approved_path=review_approved_path,
            progress_cb=progress_cb,
        )
        proposal = generated["proposal"]
        report = generated["report"]
        bundle = self.review_adapter.load(review_bundle_path)
        approved = load_approved(review_approved_path) or {}
        effective_struct = apply_struct_patches(bundle.struct, approved.get("struct_patch") or [])

        main_entry = approved.get("main_entry")
        electric_board = approved.get("electric_board")
        raw_devices = [dict(d) for d in (proposal.get("devices") or []) if isinstance(d, dict)]
        devices, grid_h, grid_w = self.resolve_devices_for_overlay(
            review_bundle_path=review_bundle_path,
            review_approved_path=review_approved_path,
            proposal_devices=raw_devices,
        )

        device_img = rgb_from_struct(effective_struct)
        device_img = upscale_rgb(device_img, PROPOSAL_RENDER_WIDTH)
        device_img = overlay_marker_icons(
            device_img,
            grid_h=effective_struct.shape[0],
            grid_w=effective_struct.shape[1],
            main_entry=main_entry,
            electric_board=electric_board,
            icon_size_px=PROPOSAL_MAP_ICON_SIZE_PX,
        )
        reserved_cells: set[tuple[int, int]] = set()
        if isinstance(main_entry, list) and len(main_entry) == 2:
            reserved_cells.add((int(main_entry[0]), int(main_entry[1])))
        if isinstance(electric_board, list) and len(electric_board) == 2:
            reserved_cells.add((int(electric_board[0]), int(electric_board[1])))
        device_img, device_counts = overlay_device_icons(
            device_img,
            grid_h=effective_struct.shape[0],
            grid_w=effective_struct.shape[1],
            devices=devices,
            icon_size_px=PROPOSAL_MAP_ICON_SIZE_PX,
            reserved_cells=reserved_cells,
        )
        overlay_path = self.artifact_store.write_rgb_image(
            workspace.proposal_level_dir(level.planner_code) / "devices_overlay_v3.png",
            device_img,
        )
        counts = report.get("device_counts") or device_counts
        total_devices = sum(int(v) for v in counts.values())
        summary = (
            f"{level.label}: {total_devices} devices placed on your floorplan to cover access and circulation—"
            "the base diagnosis stays fixed."
        )
        return ProposalViewModel(
            security_level=level.planner_code,
            devices=devices,
            overlay_path=str(overlay_path),
            counts_by_type={str(k): int(v) for k, v in counts.items()},
            proposal_summary=summary,
            proposal_path=str(generated["paths"]["proposal_path"]),
            report_path=str(generated["paths"]["report_path"]),
            grid_h=grid_h,
            grid_w=grid_w,
        )
