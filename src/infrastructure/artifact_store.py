from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


class ArtifactStore:
    def read_json(self, path: Path) -> Any:
        return json.loads(path.read_text(encoding="utf-8"))

    def write_json(self, path: Path, payload: Any) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def copy_if_exists(self, src: Path, dest: Path) -> Path | None:
        if not src.is_file():
            return None
        try:
            if src.resolve() == dest.resolve():
                return dest
        except FileNotFoundError:
            pass
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        return dest

    def write_rgb_image(self, path: Path, rgb: np.ndarray) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(rgb.astype(np.uint8)).save(path)
        return path
