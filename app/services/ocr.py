from functools import cached_property

import numpy as np


class OCRService:
    @cached_property
    def reader(self):
        import easyocr

        return easyocr.Reader(["ar", "en"], gpu=False)

    def extract_text(self, images: list[np.ndarray]) -> list[str]:
        lines: list[str] = []
        for image in images:
            results = self.reader.readtext(image, detail=0, paragraph=False)
            lines.extend(str(item).strip() for item in results if str(item).strip())
        return lines
