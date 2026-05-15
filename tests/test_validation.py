from datetime import date, timedelta

from app.services.validation import (
    MAX_UPLOAD_BYTES,
    normalize_plate_letters,
    validate_expiry_date,
    validate_upload,
    validate_vin,
)


def test_validate_vin_accepts_valid_vin():
    assert validate_vin("JTDBR32E720123456")


def test_validate_vin_rejects_forbidden_characters():
    assert not validate_vin("JTDBR32E72O123456")
    assert not validate_vin("JTDBR32E72I123456")
    assert not validate_vin("JTDBR32E72Q123456")


def test_validate_expiry_date_accepts_future_date():
    future = (date.today() + timedelta(days=30)).isoformat()
    assert validate_expiry_date(future) is None


def test_validate_expiry_date_warns_on_past_date():
    assert validate_expiry_date("2020-01-01") == "Expiry date is not in the future."


def test_validate_upload_rejects_unsupported_extension():
    assert validate_upload("card.txt", b"content") is not None


def test_validate_upload_rejects_oversized_file():
    assert validate_upload("card.jpg", b"0" * (MAX_UPLOAD_BYTES + 1)) is not None


def test_normalize_plate_letters_maps_arabic_to_english():
    assert normalize_plate_letters("أ ب ح") == ("أ ب ح", "A B J")
