from io import BytesIO
import hashlib
import os
from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener

register_heif_opener()

IMAGE_OCR_MAX_EDGE = int(os.getenv("IMAGE_OCR_MAX_EDGE", "1800"))
IMAGE_FAST_MAX_EDGE = int(os.getenv("IMAGE_FAST_MAX_EDGE", "1200"))


def is_pdf_document(filename: str, content_type: str | None = None) -> bool:
    suffix = Path(filename).suffix.lower()
    return suffix == ".pdf" or content_type == "application/pdf"


def load_document_images(content: bytes, filename: str, content_type: str | None = None) -> list[np.ndarray]:
    if is_pdf_document(filename, content_type):
        return _load_pdf_pages(content)
    return [_load_image(content)]


def extract_pdf_text(content: bytes, filename: str, content_type: str | None = None) -> list[str]:
    if not is_pdf_document(filename, content_type):
        return []

    try:
        document = fitz.open(stream=content, filetype="pdf")
    except Exception as exc:
        raise ValueError("Unsupported or unreadable PDF file.") from exc

    lines: list[str] = []
    for page in document:
        text = page.get_text("text")
        lines.extend(line.strip() for line in text.splitlines() if line.strip())
    document.close()
    return _dedupe_lines(lines)


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


def preprocess_image_variants(
    image: np.ndarray,
    include_rotations: bool = False,
    fast: bool = False,
) -> list[np.ndarray]:
    if image.size == 0:
        raise ValueError("Uploaded image is empty or unreadable.")

    cropped_image = _crop_document_region(image)
    base_images = _build_base_images(image, cropped_image, include_rotations=include_rotations)
    variants: list[np.ndarray] = []

    for base_image in base_images:
        variants.extend(_preprocess_single_image_variants(base_image, fast=fast))

    return variants


def preprocess_orientation_candidates(image: np.ndarray) -> list[np.ndarray]:
    if image.size == 0:
        raise ValueError("Uploaded image is empty or unreadable.")

    candidates: list[np.ndarray] = []
    for candidate in (
        image,
        cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE),
        cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE),
        cv2.rotate(image, cv2.ROTATE_180),
    ):
        cropped = _crop_document_region(candidate)
        candidates.extend([cropped, candidate])
    return [_limit_image_size(candidate, max_edge=IMAGE_FAST_MAX_EDGE) for candidate in _unique_images(candidates)]


def _preprocess_single_image_variants(image: np.ndarray, fast: bool = False) -> list[np.ndarray]:
    image = _limit_image_size(image)
    resized = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(resized, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    adaptive = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2,
    )
    sharpened = cv2.filter2D(
        gray,
        -1,
        np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]]),
    )
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)

    if fast:
        return [
            resized,
            clahe,
            adaptive,
        ]

    return [
        resized,
        gray,
        sharpened,
        clahe,
        adaptive,
        cv2.threshold(clahe, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
    ]


def _crop_document_region(image: np.ndarray) -> np.ndarray:
    height, width = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    mask = cv2.inRange(gray, 95, 255)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return image

    min_area = width * height * 0.20
    candidates: list[tuple[int, int, int, int]] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w * h < min_area:
            continue
        aspect_ratio = w / h if h else 0
        if 1.3 <= aspect_ratio <= 2.8:
            candidates.append((x, y, w, h))
    if not candidates:
        return image

    x, y, w, h = max(candidates, key=lambda box: box[2] * box[3])
    padding_x = int(w * 0.03)
    padding_y = int(h * 0.04)
    x1 = max(x - padding_x, 0)
    y1 = max(y - padding_y, 0)
    x2 = min(x + w + padding_x, width)
    y2 = min(y + h + padding_y, height)
    cropped = image[y1:y2, x1:x2]
    if not cropped.size:
        return image
    return cropped


def _normalize_image_orientation(image: np.ndarray) -> np.ndarray:
    if image.shape[0] > image.shape[1]:
        return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    return image


def _limit_image_size(image: np.ndarray, max_edge: int = IMAGE_OCR_MAX_EDGE) -> np.ndarray:
    height, width = image.shape[:2]
    longest_edge = max(height, width)
    if longest_edge <= max_edge:
        return image

    scale = max_edge / longest_edge
    return cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)


def _build_base_images(
    original: np.ndarray,
    cropped: np.ndarray,
    include_rotations: bool = False,
) -> list[np.ndarray]:
    if not include_rotations:
        return _unique_images([*_card_orientation_candidates(cropped), original])

    rotated_images = [
        cv2.rotate(original, cv2.ROTATE_90_CLOCKWISE),
        cv2.rotate(original, cv2.ROTATE_90_COUNTERCLOCKWISE),
        cv2.rotate(original, cv2.ROTATE_180),
    ]
    images: list[np.ndarray] = []
    for rotated_image in rotated_images:
        images.append(_crop_document_region(rotated_image))
        images.append(rotated_image)
    return _unique_images(images)


def _card_orientation_candidates(image: np.ndarray) -> list[np.ndarray]:
    if image.shape[0] <= image.shape[1]:
        return [image, cv2.rotate(image, cv2.ROTATE_180)]

    return [
        cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE),
        cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE),
        image,
    ]

def _unique_images(images: list[np.ndarray]) -> list[np.ndarray]:
    unique: list[np.ndarray] = []
    seen_signatures: set[str] = set()
    for image in images:
        signature = _image_signature(image)
        if signature in seen_signatures:
            continue
        seen_signatures.add(signature)
        unique.append(image)
    return unique


def _image_signature(image: np.ndarray) -> str:
    step_y = max(image.shape[0] // 32, 1)
    step_x = max(image.shape[1] // 32, 1)
    sample = np.ascontiguousarray(image[::step_y, ::step_x])
    digest = hashlib.blake2b(sample.tobytes(), digest_size=8).hexdigest()
    return f"{image.shape}:{digest}"


def _load_image(content: bytes) -> np.ndarray:
    try:
        with Image.open(BytesIO(content)) as image:
            image = ImageOps.exif_transpose(image)
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
