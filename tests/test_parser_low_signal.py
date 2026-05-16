from app.services.parser import parse_istimara


def test_low_signal_ocr_noise_does_not_create_fake_card_fields():
    data, warnings = parse_istimara(
        [
            "5:45",
            "\u0631\u062e\u0635\u0629 \u0633\u064a\u0631",
            "9",
            "\u0669",
            "\u062f",
            "\u064a",
            "\u061f",
            "\u061f [",
            "\u064b",
            "\u0645",
            "[",
            "\u0664",
            "\u0645\u064b[\u064b",
            "\u0666",
            "@",
            "\u062b\u0629\u064b \u0628\u0629\u0643 \u0628\u061f",
            "5",
            ".(",
            "\u061f \u061f",
            "\u0645\u062d",
            "\u0633\u064a\u0631",
            "\u0668",
            "\u062b\u0629\u064b \u0628\u0629\u0643 \u0628",
            "\u0631\u062e\u0635\u0629",
            "\u0662\u0660",
            ";5845",
            "66.",
        ]
    )

    assert data.model_dump(exclude_none=True) == {}
    assert warnings == ["OCR completed, but no supported Istimara fields were confidently extracted."]
