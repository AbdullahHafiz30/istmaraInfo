import os
from functools import cached_property
from pathlib import Path

import numpy as np


class OCRService:
    requires_preprocessing = True

    def __init__(self, model_storage_directory: str | Path | None = None) -> None:
        base_directory = Path(
            model_storage_directory
            or os.getenv("EASYOCR_MODEL_DIR")
            or Path.cwd() / ".easyocr"
        )
        self.model_storage_directory = base_directory / "model"
        self.user_network_directory = base_directory / "user_network"

    @cached_property
    def reader(self):
        import easyocr

        try:
            self.model_storage_directory.mkdir(parents=True, exist_ok=True)
            self.user_network_directory.mkdir(parents=True, exist_ok=True)
            return easyocr.Reader(
                ["ar", "en"],
                gpu=os.getenv("EASYOCR_GPU", "false").lower() in {"1", "true", "yes"},
                model_storage_directory=str(self.model_storage_directory),
                user_network_directory=str(self.user_network_directory),
                verbose=False,
            )
        except Exception as exc:
            raise RuntimeError(
                "OCR engine failed to initialize. Check EasyOCR model folder permissions "
                "and internet access for the first model download."
            ) from exc

    def extract_text(self, images: list[np.ndarray]) -> list[str]:
        lines: list[str] = []
        for image in images:
            results = self.reader.readtext(image, detail=0, paragraph=False)
            lines.extend(str(item).strip() for item in results if str(item).strip())
        return _dedupe_lines(lines)


def _dedupe_lines(lines: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for line in lines:
        normalized = line.casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        unique.append(line)
    return unique
