from datetime import date, datetime
from pathlib import Path

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".pdf"}

AR_TO_EN_PLATE = {
    "ا": "A",
    "أ": "A",
    "ب": "B",
    "ح": "J",
    "د": "D",
    "ر": "R",
    "س": "S",
    "ص": "X",
    "ط": "T",
    "ع": "E",
    "ق": "G",
    "ك": "K",
    "ل": "L",
    "م": "Z",
    "ن": "N",
    "ه": "H",
    "و": "U",
    "ى": "V",
}
EN_TO_AR_PLATE = {value: key for key, value in AR_TO_EN_PLATE.items() if key != "أ"}


def validate_upload(filename: str | None, content: bytes) -> str | None:
    if not filename:
        return "Missing filename."

    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        return "Unsupported file type. Supported formats: JPG, JPEG, PNG, HEIC, PDF."

    if not content:
        return "Uploaded file is empty."

    if len(content) > MAX_UPLOAD_BYTES:
        return "Uploaded file exceeds the 10MB size limit."

    return None


def validate_vin(vin: str | None) -> bool:
    if not vin:
        return False
    vin = vin.upper()
    if len(vin) != 17:
        return False
    if any(char in vin for char in ("I", "O", "Q")):
        return False
    return vin.isalnum()


def validate_expiry_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        expiry = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return "Expiry date was detected but could not be normalized."

    if expiry <= date.today():
        return "Expiry date is not in the future."
    return None


def normalize_plate_letters(text: str) -> tuple[str | None, str | None]:
    ar_letters = [char for char in text if char in AR_TO_EN_PLATE]
    if ar_letters:
        ar_value = " ".join(ar_letters[:3])
        en_value = " ".join(AR_TO_EN_PLATE[char] for char in ar_letters[:3])
        return ar_value, en_value

    en_letters = _extract_spaced_plate_letters(text)
    ar_value = " ".join(EN_TO_AR_PLATE[char] for char in en_letters) if en_letters else None
    en_value = " ".join(en_letters) if en_letters else None

    return ar_value, en_value


def _extract_spaced_plate_letters(text: str) -> list[str]:
    allowed = set(EN_TO_AR_PLATE)
    tokens = [token.upper() for token in text.replace("-", " ").split()]
    single_letter_tokens = [token for token in tokens if len(token) == 1 and token in allowed]
    return single_letter_tokens[:3] if len(single_letter_tokens) >= 2 else []
