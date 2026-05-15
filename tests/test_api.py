from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class FakeOCRService:
    def extract_text(self, images):
        return [
            "Plate 1234 أ ب ح",
            "VIN JTDBR32E720123456",
            "Toyota Camry 2023 White",
            "Expiry 2099-05-01",
        ]


def test_extract_istimara_rejects_missing_file():
    response = client.post("/extract-istimara")

    assert response.status_code == 422


def test_extract_istimara_rejects_unsupported_file_type():
    response = client.post(
        "/extract-istimara",
        files={"file": ("card.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_extract_istimara_returns_response_shape(monkeypatch):
    from app import main

    monkeypatch.setattr(main, "ocr_service", FakeOCRService())
    response = client.post(
        "/extract-istimara",
        files={
            "file": (
                "card.png",
                _tiny_png(),
                "image/png",
            )
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["plate_number"] == "1234"
    assert body["data"]["vin"] == "JTDBR32E720123456"
    assert body["warnings"] == []


def _tiny_png() -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
        b"\x00\x00\x00\x0cIDATx\x9cc\xf8\xff\xff?\x00\x05"
        b"\xfe\x02\xfeA\xe2'5\x00\x00\x00\x00IEND\xaeB`\x82"
    )
