from app.models import ExtractResponse
from app.services.ocr import OCRService
from app.services.parser import parse_istimara
from app.services.preprocess import load_document_images, preprocess_image


def extract_istimara(
    content: bytes,
    filename: str,
    content_type: str | None,
    ocr_service: OCRService,
) -> ExtractResponse:
    images = load_document_images(content, filename, content_type)
    processed_images = [preprocess_image(image) for image in images]
    lines = ocr_service.extract_text(processed_images)
    data, warnings = parse_istimara(lines)
    return ExtractResponse(success=True, data=data, warnings=warnings)
