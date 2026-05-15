from app.services.parser import parse_istimara


def test_parse_istimara_extracts_year_plate_and_vin():
    data, warnings = parse_istimara(
        [
            "Plate 1234 أ ب ح",
            "VIN JTDBR32E720123456",
            "Toyota Camry 2023 White",
            "Expiry 2099-05-01",
        ]
    )

    assert data.plate_number == "1234"
    assert data.plate_text_ar == "أ ب ح"
    assert data.plate_text_en == "A B J"
    assert data.vin == "JTDBR32E720123456"
    assert data.model_year == "2023"
    assert data.vehicle_make == "Toyota"
    assert data.color == "White"
    assert data.expiry_date == "2099-05-01"
    assert warnings == []


def test_parse_istimara_returns_warning_when_no_fields_found():
    data, warnings = parse_istimara(["unrelated text"])

    assert data.model_dump() == {
        "plate_number": None,
        "plate_text_ar": None,
        "plate_text_en": None,
        "registration_number": None,
        "serial_number": None,
        "vehicle_make": None,
        "vehicle_model": None,
        "model_year": None,
        "color": None,
        "vin": None,
        "owner_name": None,
        "expiry_date": None,
    }
    assert warnings == ["OCR completed, but no supported Istimara fields were confidently extracted."]
