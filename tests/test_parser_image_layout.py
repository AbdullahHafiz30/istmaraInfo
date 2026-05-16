from app.services.parser import parse_istimara


def test_parse_image_layout_prefers_full_owner_and_continuous_serial():
    data, warnings = parse_istimara(
        [
            "\u0639\u0628\u062f\u0627\u0644\u0627\u0644\u0647 \u0628\u0646 \u0645\u062d\u0645\u062f\u0628\u0646 \u0632\u0643\u0631\u064a\u0627 \u062d\u0627\u0641\u0638",
            "\u0627\u0644\u0645\u0627\u0644\u0643",
            "\u0628\u0646 \u0645\u062d\u0645\u062f \u0628\u0646 \u0632\u0643\u0631\u064a\u0627 \u062d\u0627\u0641\u0638",
            "\u0661\u0660\u0669\u0668\u0661\u0660\u0662\u0668\u0666\u0664",
            "2FAFP73W36X109941",
            "1951 7 T A",
            "\u0641\u064a\u0643\u062a\u0648\u0631\u064a\u0627",
            "\u0641\u0648\u0631\u062f",
            "\u0660\u0666",
            "\u0633\u0646\u0629 \u0627\u0644\u0635\u0646\u0639",
            "\u0627\u062e\u0636\u0631",
            "\u0664\u0663\u0665\u0668\u0662\u0663\u0667",
            "\u0631\u0642\u0645",
            "\u0627\u0644\u0645\u0633\u062a\u062e\u062f\u0645",
            "\u0639\u0628\u062f\u0627\u0644\u0644\u0647",
            "\u0627\u062e\u0636\u0631",
            "\u0627\u0644\u062a\u0633\u0644\u0633\u0644\u0649",
            "\u0662\u0668\u0666\u0664 \u0669\u0668\u0661\u0660",
            "\u0647\u0648\u064a\u0629",
            "\u0664\u0663\u0665\u0668\u0662\u0663\u0667\u0660",
            "\u0631\u0642\u0645 \u0627\u0644\u062a\u0633\u0644\u0633\u0644\u0649",
        ]
    )

    assert data.owner_name == "\u0639\u0628\u062f\u0627\u0644\u0627\u0644\u0647 \u0628\u0646 \u0645\u062d\u0645\u062f\u0628\u0646 \u0632\u0643\u0631\u064a\u0627 \u062d\u0627\u0641\u0638"
    assert data.user_name == "\u0639\u0628\u062f\u0627\u0644\u0644\u0647 \u0628\u0646 \u0645\u062d\u0645\u062f\u0628\u0646 \u0632\u0643\u0631\u064a\u0627 \u062d\u0627\u0641\u0638"
    assert data.user_id == "1098102864"
    assert data.serial_number == "435823700"
    assert data.vin == "2FAFP73W36X109941"
    assert warnings == ["Some important fields were not extracted: expiry_date."]
