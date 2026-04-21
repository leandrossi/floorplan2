from __future__ import annotations

from pathlib import Path

import numpy as np

from domain.contracts import RiskViewModel
from infrastructure.artifact_store import ArtifactStore
from infrastructure.review_bundle_adapter import ReviewBundleAdapter
from review_bundle_io import apply_struct_patches, load_approved
from ui_components import alpha_blend, overlay_markers, rgb_from_struct, compute_pre_suppression_red_mask

FIXED_RISK_LEVEL = "optimal"


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
            raise RuntimeError("Falta la revisión aprobada para construir el diagnóstico.")

        effective_struct = apply_struct_patches(bundle.struct, approved.get("struct_patch") or [])
        main_entry = approved.get("main_entry")
        electric_board = approved.get("electric_board")

        base_rgb = overlay_markers(
            rgb_from_struct(effective_struct),
            main_entry=main_entry,
            electric_board=electric_board,
            marker_radius=2,
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
                risk_rgb = alpha_blend(risk_rgb, red_mask, (220, 20, 60), alpha=0.42)
        risk_overlay_path = self.artifact_store.write_rgb_image(output_path, risk_rgb)

        if red_cells > 0:
            summary = (
                "Marcamos en rojo las áreas más expuestas según accesos y circulación. "
                "Este diagnóstico base queda fijo y después te mostramos distintas formas de cubrirlo."
            )
            details = [f"Área diagnosticada: {red_cells} celdas del plano."]
        else:
            summary = (
                "No detectamos zonas rojas persistentes en esta vista base. "
                "Igual te mostramos una solución recomendada para cubrir accesos y circulación."
            )
            details = ["El motor no dejó zonas rojas después del diagnóstico base."]

        return RiskViewModel(
            base_plan_path=str(base_plan_path),
            risk_overlay_path=str(risk_overlay_path),
            legend=[
                {"label": "Diagnóstico base", "color": "Rojo translúcido"},
                {"label": "Entrada principal", "color": "Rojo sólido"},
                {"label": "Cuadro eléctrico", "color": "Azul sólido"},
            ],
            summary_text=summary,
            details=details,
        )
