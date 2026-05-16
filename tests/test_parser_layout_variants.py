from app.services.parser import parse_istimara


def test_parse_owner_only_layout_with_shifted_phone_screenshot_ocr():
    data, warnings = parse_istimara(
        [
            "\u0639\u0644\u0649 \u0628\u0646 \u0633\u0639\u062f \u0627\u0644\u0635\u0628\u064a\u0627\u0646\u0649",
            "\u0648\u0641\u0627\u0621",
            "\u0627\u0644\u0645\u0627\u0644\u0643",
            "\u0647\u0648\u064a\u0629",
            "\u0662\u0666\u0665\u0668\u0663\u0662\u0661 \u0661 \u0661\u0661",
            "\u0647\u0648\u064a\u0629 \u0627\u0644\u0645\u0627\u0644\u0643",
            "IM7DMAW70T0322261",
            "\u0631\u0642\u0645 \u0627\u0644\u0647\u064a\u0643\u0644",
            "\u062f \u0628 \u0664\u0661\u0667\u0668",
            "\u0631\u0642\u0645 \u0627\u0644\u0644\u0648\u062d\u0629",
            "\u0633",
            "4178",
            "8 D $",
            "CX-30",
            "\u0637\u0631\u0627\u0632 \u0627\u0644\u0645\u0631\u0643\u0628\u0629",
            "\u0645\u0627\u0632\u062f\u0627",
            "\u0645\u0627\u0631\u0643\u0629 \u0627\u0644\u0645\u0631\u0643\u0628\u0629",
            "\u0662\u0660\u0662\u0666",
            "\u0633\u0646\u0629 \u0627\u0644\u0635\u0646\u0639",
            "\u0627\u0632\u0631\u0642 \u063a\u0627\u0645\u0642",
            "\u0627\u0644\u0644\u0648\u0646",
            "\u0664\u0665\u0666\u0663\u0666\u0665\u0662\u0662",
            "\u0631\u0642\u0645 \u0627\u0644\u062a\u0633\u0644\u0633\u0644\u0649",
            "JM7DMAW70T0322261",
        ]
    )

    assert data.plate_number == "4178"
    assert data.plate_text_ar == "\u0628 \u062f \u0633"
    assert data.plate_text_en == "B D S"
    assert data.serial_number == "456365220"
    assert data.vehicle_make == "Mazda"
    assert data.vehicle_model == "CX-30"
    assert data.model_year == "2026"
    assert data.color == "Dark Blue"
    assert data.vin == "JM7DMAW70T0322261"
    assert data.owner_name == "\u0648\u0641\u0627\u0621 \u0628\u0646\u062a \u0639\u0644\u064a \u0628\u0646 \u0633\u0639\u062f \u0627\u0644\u0635\u0628\u064a\u0627\u0646\u064a"
    assert data.user_name is None
    assert data.owner_id == "1112658321"
    assert warnings == ["Some important fields were not extracted: expiry_date."]
