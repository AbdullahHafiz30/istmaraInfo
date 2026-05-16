import fitz

from app.services.pipeline import extract_istimara
from app.services.preprocess import preprocess_image_variants


class CapturingOCRService:
    requires_preprocessing = True

    def __init__(self) -> None:
        self.image_count = 0

    def extract_text(self, images):
        self.image_count = len(images)
        return []


def test_pipeline_uses_selectable_pdf_text_before_ocr():
    service = CapturingOCRService()
    response = extract_istimara(
        content=_pdf_with_text("VIN 2FAFP73W36X109941\nCar Year\n2006\n1951 Z T A"),
        filename="card.pdf",
        content_type="application/pdf",
        ocr_service=service,
        include_raw_text=True,
    )

    assert response.data.vin == "2FAFP73W36X109941"
    assert response.data.model_year == "2006"
    assert "VIN 2FAFP73W36X109941" in (response.raw_text or [])
    assert service.image_count >= 1


def test_preprocess_image_variants_returns_multiple_passes():
    import numpy as np

    image = np.full((16, 16, 3), 255, dtype=np.uint8)
    variants = preprocess_image_variants(image)

    assert len(variants) >= 5


def test_pipeline_retries_images_with_rotations_only_after_empty_first_parse():
    service = RetryingOCRService()
    response = extract_istimara(
        content=_tiny_png(),
        filename="rotated-card.png",
        content_type="image/png",
        ocr_service=service,
        include_raw_text=True,
    )

    assert service.calls >= 2
    assert response.data.vin == "JTDBR32E720123456"
    assert response.data.plate_number == "1234"
    assert "Expiry 2099-05-01" in (response.raw_text or [])


def _pdf_with_text(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    data = document.tobytes()
    document.close()
    return data


class RetryingOCRService:
    requires_preprocessing = True

    def __init__(self) -> None:
        self.calls = 0

    def extract_text(self, images):
        self.calls += 1
        if self.calls == 1:
            return ["؟", "رخصة سير"]
        return [
            "Plate 1234 أ ب ح",
            "VIN JTDBR32E720123456",
            "Toyota Camry 2023 White",
            "Expiry 2099-05-01",
        ]


def _tiny_png() -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
        b"\x00\x00\x00\x0cIDATx\x9cc\xf8\xff\xff?\x00\x05"
        b"\xfe\x02\xfeA\xe2'5\x00\x00\x00\x00IEND\xaeB`\x82"
    )
