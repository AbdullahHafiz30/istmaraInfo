from app.models import ExtractResponse
from app.services.ocr import OCRService
from app.services.parser import parse_istimara
from app.services.preprocess import (
    extract_pdf_text,
    is_pdf_document,
    load_document_images,
    preprocess_orientation_candidates,
    preprocess_image_variants,
)


def extract_istimara(
    content: bytes,
    filename: str,
    content_type: str | None,
    ocr_service: OCRService,
    include_raw_text: bool = False,
) -> ExtractResponse:
    is_pdf = is_pdf_document(filename, content_type)
    pdf_lines = extract_pdf_text(content, filename, content_type)
    images = load_document_images(content, filename, content_type)

    if is_pdf:
        ocr_lines = _extract_image_lines(images, ocr_service=ocr_service, fast=False)
        lines = _dedupe_lines([*pdf_lines, *ocr_lines])
        data, warnings = parse_istimara(lines)
    else:
        lines, data, warnings = _extract_image_data(
            base_lines=pdf_lines,
            images=images,
            ocr_service=ocr_service,
        )

    return ExtractResponse(
        success=True,
        data=data,
        warnings=warnings,
        raw_text=lines if include_raw_text else None,
    )


def _extract_image_data(
    base_lines: list[str],
    images,
    ocr_service: OCRService,
):
    lines = _dedupe_lines(base_lines)
    data, warnings = parse_istimara(lines)

    stages = (
        {"fast": True, "include_rotations": False, "target_score": 6},
        {"fast": False, "include_rotations": False, "target_score": 6},
    )

    for stage in stages:
        candidate_lines = _extract_image_lines_progressively(
            images,
            ocr_service=ocr_service,
            base_lines=lines,
            fast=stage["fast"],
            include_rotations=stage["include_rotations"],
            target_score=stage["target_score"],
        )
        lines, data, warnings = _use_better_parse(lines, data, warnings, candidate_lines)
        if _extraction_score(data) >= stage["target_score"]:
            break

    if _extraction_score(data) == 0:
        orientation_lines = _extract_orientation_candidate_lines(images, ocr_service=ocr_service)
        lines, data, warnings = _use_better_parse(lines, data, warnings, orientation_lines)

    return lines, data, warnings


def _extract_image_lines(
    images,
    ocr_service: OCRService,
    include_rotations: bool = False,
    fast: bool = False,
) -> list[str]:
    if getattr(ocr_service, "requires_preprocessing", True):
        ocr_images = [
            variant
            for image in images
            for variant in preprocess_image_variants(
                image,
                include_rotations=include_rotations,
                fast=fast,
            )
        ]
    else:
        ocr_images = images
    return ocr_service.extract_text(ocr_images)


def _extract_image_lines_progressively(
    images,
    ocr_service: OCRService,
    base_lines: list[str],
    include_rotations: bool = False,
    fast: bool = False,
    target_score: int = 6,
) -> list[str]:
    if not getattr(ocr_service, "requires_preprocessing", True):
        return ocr_service.extract_text(images)

    variants = [
        variant
        for image in images
        for variant in preprocess_image_variants(
            image,
            include_rotations=include_rotations,
            fast=fast,
        )
    ]
    stage_lines: list[str] = []
    for variant in variants:
        stage_lines = _dedupe_lines([*stage_lines, *ocr_service.extract_text([variant])])
        candidate_lines = _dedupe_lines([*base_lines, *stage_lines])
        candidate_data, _ = parse_istimara(candidate_lines)
        if _extraction_score(candidate_data) >= target_score:
            break
    return stage_lines


def _extract_orientation_candidate_lines(images, ocr_service: OCRService) -> list[str]:
    if getattr(ocr_service, "requires_preprocessing", True):
        ocr_images = [candidate for image in images for candidate in preprocess_orientation_candidates(image)]
    else:
        ocr_images = images
    return ocr_service.extract_text(ocr_images)


def _use_better_parse(
    lines: list[str],
    data,
    warnings: list[str],
    candidate_lines: list[str],
):
    merged_lines = _dedupe_lines([*lines, *candidate_lines])
    candidate_data, candidate_warnings = parse_istimara(merged_lines)
    if _extraction_score(candidate_data) > _extraction_score(data):
        return merged_lines, candidate_data, candidate_warnings
    return merged_lines, data, warnings


def _extraction_score(data) -> int:
    priority_fields = (
        "vin",
        "plate_number",
        "owner_name",
        "owner_id",
        "user_id",
        "serial_number",
        "vehicle_make",
        "vehicle_model",
        "model_year",
    )
    return sum(1 for field in priority_fields if getattr(data, field) is not None)


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
