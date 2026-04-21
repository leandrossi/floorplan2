from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from infrastructure.artifact_store import ArtifactStore


@dataclass
class ReviewBundleData:
    bundle_path: Path
    step04_dir: Path
    grid_shape: tuple[int, int]
    cell_size_m: float
    struct: np.ndarray
    preview_image_path: Path | None


class ReviewBundleAdapter:
    def __init__(self, artifact_store: ArtifactStore | None = None) -> None:
        self.artifact_store = artifact_store or ArtifactStore()

    def load(self, bundle_path: Path) -> ReviewBundleData:
        bundle = self.artifact_store.read_json(bundle_path)
        struct = np.asarray(bundle["struct"], dtype=np.uint8)
        preview_name = str(bundle.get("preview_image") or "").strip()
        preview_path = bundle_path.parent / preview_name if preview_name else None
        return ReviewBundleData(
            bundle_path=bundle_path,
            step04_dir=Path(bundle["step04_dir"]),
            grid_shape=(int(struct.shape[0]), int(struct.shape[1])),
            cell_size_m=float(bundle.get("cell_size_m", 0.05)),
            struct=struct,
            preview_image_path=preview_path if preview_path and preview_path.is_file() else None,
        )
