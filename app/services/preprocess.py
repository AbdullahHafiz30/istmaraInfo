from io import BytesIO
from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()


def load_document_images(content: bytes, filename: str, content_type: str | None = None) -> list[np.ndarray]:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf" or content_type == "application/pdf":
        return _load_pdf_pages(content)
    return [_load_image(content)]


def preprocess_image(image: np.ndarray) -> np.ndarray:
    if image.size == 0:
        raise ValueError("Uploaded image is empty or unreadable.")

    resized = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(resized, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    return cv2.adaptiveThreshold(
        blur,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2,
    )


def _load_image(content: bytes) -> np.ndarray:
    try:
        with Image.open(BytesIO(content)) as image:
            return np.array(image.convert("RGB"))
    except Exception as exc:
        raise ValueError("Unsupported or unreadable image file.") from exc


def _load_pdf_pages(content: bytes) -> list[np.ndarray]:
    try:
        document = fitz.open(stream=content, filetype="pdf")
    except Exception as exc:
        raise ValueError("Unsupported or unreadable PDF file.") from exc

    if document.page_count == 0:
        raise ValueError("PDF does not contain any pages.")

    images: list[np.ndarray] = []
    for page in document:
        pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
        images.append(np.array(image))
    document.close()
    return images
