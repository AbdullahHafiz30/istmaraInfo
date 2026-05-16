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
        "owner_id": None,
        "user_name": None,
        "user_id": None,
        "expiry_date": None,
        "expiry_date_hijri": None,
    }
    assert warnings == ["OCR completed, but no supported Istimara fields were confidently extracted."]


def test_parse_istimara_warns_when_important_fields_are_missing():
    data, warnings = parse_istimara(["Plate 1951 م ر ا", "owner . هراية"])

    assert data.plate_number == "1951"
    assert data.owner_name is None
    assert warnings == ["Some important fields were not extracted: vin, vehicle_make, model_year, expiry_date."]


def test_parse_istimara_normalizes_arabic_digits_and_separates_hijri_date():
    data, warnings = parse_istimara(
        [
            "Plate ٠٩٨ و ك ل",
            "VIN 2FAFP73W36X109941",
            "Model Year 2006",
            "Owner ID Number",
            "Expiry 1426-12-04",
        ]
    )

    assert data.plate_number == "098"
    assert data.plate_text_ar == "و ك ل"
    assert data.plate_text_en == "U K L"
    assert data.model_year == "2006"
    assert data.vin == "2FAFP73W36X109941"
    assert data.vehicle_make == "Ford"
    assert data.owner_name is None
    assert data.expiry_date is None
    assert data.expiry_date_hijri == "1426-12-04"
    assert warnings == [
        "Hijri-looking expiry date was detected; Gregorian conversion is required before using expiry_date.",
        "Some important fields were not extracted: expiry_date.",
    ]


def test_parse_istimara_uses_vin_year_code_when_ocr_year_is_missing():
    data, warnings = parse_istimara(["VIN 2FAFP73W36X109941", "Ford Green"])

    assert data.model_year == "2006"
    assert warnings == ["Some important fields were not extracted: expiry_date."]


def test_parse_istimara_repairs_leading_j_read_as_i_in_vin():
    data, warnings = parse_istimara(["IM7DMAW70T0322261", "مازدا", "2026"])

    assert data.vin == "JM7DMAW70T0322261"
    assert data.vehicle_make == "Mazda"
    assert data.model_year == "2026"
    assert warnings == ["Some important fields were not extracted: expiry_date."]


def test_parse_tawakkalna_pdf_raw_text_extracts_labeled_fields():
    data, warnings = parse_istimara(
        [
            "Owner",
            "ID Number",
            "المالك",
            "عبدالاله بن محمدبن زكريا حافظ",
            "1012331201",
            "Car Model / طراز المركبة",
            "Car Name / ماركة المركبة",
            "فيكتوريا",
            "Car Register Number",
            "رقم الهيكل",
            "Car Year",
            "سنة الصنع",
            "2FAFP73W36X109941",
            "2006",
            "Plate Number in Arabic",
            "رقم اللوحة",
            "Car Serial Number",
            "الرقم التسلسلي",
            "أط م 1951",
            "435823700",
            "Car Color",
            "لون المركبة",
            "Plate number",
            "رقم اللوحة بالإنجليزي",
            "1951 Z T A",
            "فورد",
            "اخضر",
            "Issue Date",
            "تاريخ الإصدار",
            "04/01/2006",
            "Expire Date",
            "تاريخ الانتهاء",
            "Issue Date in Hijri / تاريخ الإصدار بالهجري",
            "18/04/2029",
            "1426/12/04",
            "Expire Date in Hijri / تاريخ الانتهاء بالهجري",
            "لا يوجد",
            "1450/12/04",
        ]
    )

    assert data.plate_number == "1951"
    assert data.plate_text_ar == "م ط ا"
    assert data.plate_text_en == "Z T A"
    assert data.serial_number == "435823700"
    assert data.vehicle_make == "Ford"
    assert data.vehicle_model == "Victoria"
    assert data.model_year == "2006"
    assert data.color == "Green"
    assert data.vin == "2FAFP73W36X109941"
    assert data.owner_name == "عبدالاله بن محمدبن زكريا حافظ"
    assert data.expiry_date == "2029-04-18"
    assert data.expiry_date_hijri == "1450-12-04"
    assert warnings == []


def test_parse_image_raw_text_warns_for_invalid_vin_like_text():
    data, warnings = parse_istimara(
        [
            "المالك .",
            "هراية المالك",
            "2FAFP73TNB6NO994l",
            "رقم الهيكل",
            ";1951;27:4",
            "اراا",
        ]
    )

    assert data.vin is None
    assert data.owner_name is None
    assert "VIN-like text was detected but failed validation." in warnings


def test_parse_improved_image_raw_text_prefers_best_vin_and_two_digit_year():
    data, warnings = parse_istimara(
        [
            "عبدالاله بن محمدبن زكريا حافظ",
            "المالك",
            "بن محمد بن زكريا حافظ",
            "١٠٩٨١٠٢٨٦٤",
            "2FAFP73T36X109941",
            "رقم الهيكل",
            "١٩٥١",
            "رقم اللوحة",
            "1951 7 T A",
            "فيكتوريا",
            "فورد",
            "٠٦",
            "سنة الصنع",
            "اخضر",
            "2FAFP73W36X109941",
        ]
    )

    assert data.plate_number == "1951"
    assert data.plate_text_ar == "م ط ا"
    assert data.plate_text_en == "Z T A"
    assert data.registration_number is None
    assert data.vehicle_make == "Ford"
    assert data.vehicle_model == "Victoria"
    assert data.model_year == "2006"
    assert data.color == "Green"
    assert data.vin == "2FAFP73W36X109941"
    assert data.owner_id is None
    assert data.user_id == "1098102864"
    assert warnings == ["Some important fields were not extracted: expiry_date."]


def test_parse_fixed_layout_identity_and_serial_fields():
    data, warnings = parse_istimara(
        [
            "عبدالاله بن محمدبن زكريا حافظ",
            "المالك",
            "١٠٩٨١٠٢٨٦٤",
            "هوية",
            "٤٣٥٨٢٣٧",
            "رقم التسلسلى",
            "المستخدم",
            "عبدالله بن محمدبن زكريا حافظ",
            "2FAFP73W36X109941",
            "1951 7 T A",
            "فورد",
            "فيكتوريا",
            "٠٦",
            "سنة الصنع",
            "اخضر",
        ]
    )

    assert data.owner_name == "عبدالاله بن محمدبن زكريا حافظ"
    assert data.owner_id is None
    assert data.user_name == "عبدالله بن محمدبن زكريا حافظ"
    assert data.user_id == "1098102864"
    assert data.registration_number is None
    assert data.serial_number == "435823700"
    assert data.vin == "2FAFP73W36X109941"
    assert warnings == ["Some important fields were not extracted: expiry_date."]


def test_parse_tawakkalna_pdf_does_not_use_user_id_as_registration_number():
    data, warnings = parse_istimara(
        [
            "ﺳٮ\"ﺮ رﺣ'ﺼﺔ",
            "Vehicle Registration",
            "ID Number / المالك هوية",
            "1012331201",
            "Owner / الاسم",
            "ﺣﺎڡ.ﻆ زﻛريﺎ ٮ5ﻦ ﻣﺤﻤﺪ ٮ5ﻦ ﻋٮ5ﺪاﻻﻟﻪ",
            "Co Owner ID / المستخدم هوية",
            "1098102864",
            "Co Owner Name / المستخدم",
            "ﺣﺎڡ.ﻆ زﻛريﺎ ٮ5ﻦ ﻣﺤﻤﺪ ٮ5ﻦ ﻋٮ5ﺪﷲ",
            "Owner",
            "ID Number",
            "عبدالاله بن محمدبن زكريا حافظ",
            "Co Owner Name /",
            "المستخدم",
            "Co Owner ID /",
            "عبدالله بن محمدبن زكريا حافظ",
        ]
    )

    assert data.registration_number is None
    assert data.owner_name == "عبدالاله بن محمدبن زكريا حافظ"
    assert data.user_name == "عبدالله بن محمدبن زكريا حافظ"
    assert data.user_id == "1098102864"
    assert data.owner_id == "1012331201"
    assert warnings == ["Some important fields were not extracted: vin, vehicle_make, model_year, expiry_date."]
