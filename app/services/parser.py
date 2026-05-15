import re
from datetime import date, datetime

from app.models import IstimaraData
from app.services.validation import normalize_plate_letters, validate_expiry_date, validate_vin

VIN_RE = re.compile(r"\b[A-HJ-NPR-Z0-9]{17}\b", re.IGNORECASE)
YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
PLATE_NUMBER_RE = re.compile(r"\b\d{1,4}\b")
LONG_NUMBER_RE = re.compile(r"\b\d{6,12}\b")
ISO_DATE_RE = re.compile(r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b")
DMY_DATE_RE = re.compile(r"\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\b")

KNOWN_MAKES = (
    "Toyota",
    "Hyundai",
    "Honda",
    "Nissan",
    "Ford",
    "Chevrolet",
    "Kia",
    "Mazda",
    "Lexus",
    "Mercedes",
    "BMW",
    "GMC",
)

KNOWN_COLORS = (
    "White",
    "Black",
    "Silver",
    "Gray",
    "Grey",
    "Red",
    "Blue",
    "Green",
    "Brown",
    "Gold",
)


def parse_istimara(lines: list[str]) -> tuple[IstimaraData, list[str]]:
    warnings: list[str] = []
    normalized_lines = [_clean_line(line) for line in lines if _clean_line(line)]
    full_text = "\n".join(normalized_lines)

    vin = _first_match(VIN_RE, full_text)
    if vin:
        vin = vin.upper()
        if not validate_vin(vin):
            warnings.append("VIN was detected but failed validation.")
            vin = None

    expiry_date = _extract_date(full_text)
    if expiry_date:
        expiry_warning = validate_expiry_date(expiry_date)
        if expiry_warning:
            warnings.append(expiry_warning)

    plate_ar, plate_en = normalize_plate_letters(full_text)

    data = IstimaraData(
        plate_number=_extract_plate_number(full_text),
        plate_text_ar=plate_ar,
        plate_text_en=plate_en,
        registration_number=_extract_number_after_keywords(normalized_lines, ("registration", "رخصة", "استمارة")),
        serial_number=_extract_number_after_keywords(normalized_lines, ("serial", "sequence", "تسلسل", "مسلسل")),
        vehicle_make=_extract_known_value(full_text, KNOWN_MAKES),
        vehicle_model=_extract_vehicle_model(normalized_lines),
        model_year=_extract_year(full_text),
        color=_extract_known_value(full_text, KNOWN_COLORS),
        vin=vin,
        owner_name=_extract_owner_name(normalized_lines),
        expiry_date=expiry_date,
    )

    if not any(value is not None for value in data.model_dump().values()):
        warnings.append("OCR completed, but no supported Istimara fields were confidently extracted.")

    return data, warnings


def _clean_line(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip()


def _first_match(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    return match.group(0) if match else None


def _extract_year(text: str) -> str | None:
    current_year = date.today().year
    for match in YEAR_RE.finditer(text):
        year = int(match.group(0))
        if 1980 <= year <= current_year + 1:
            return str(year)
    return None


def _extract_plate_number(text: str) -> str | None:
    for match in PLATE_NUMBER_RE.finditer(text):
        number = match.group(0)
        if 1 <= len(number) <= 4:
            return number
    return None


def _extract_number_after_keywords(lines: list[str], keywords: tuple[str, ...]) -> str | None:
    lowered_keywords = tuple(keyword.lower() for keyword in keywords)
    for index, line in enumerate(lines):
        haystack = line.lower()
        if any(keyword in haystack for keyword in lowered_keywords):
            search_area = " ".join(lines[index : index + 2])
            match = LONG_NUMBER_RE.search(search_area)
            if match:
                return match.group(0)
    return None


def _extract_known_value(text: str, values: tuple[str, ...]) -> str | None:
    for value in values:
        if re.search(rf"\b{re.escape(value)}\b", text, re.IGNORECASE):
            return value
    return None


def _extract_vehicle_model(lines: list[str]) -> str | None:
    for line in lines:
        match = re.search(r"\bmodel\s*[:\-]?\s*([A-Za-z][A-Za-z0-9 -]{1,30})", line, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _extract_owner_name(lines: list[str]) -> str | None:
    for index, line in enumerate(lines):
        if re.search(r"\bowner\b|المالك|اسم", line, re.IGNORECASE):
            combined = " ".join(lines[index : index + 2])
            combined = re.sub(r"\bowner\b|name|المالك|اسم|[:\-]", " ", combined, flags=re.IGNORECASE)
            combined = _clean_line(combined)
            if combined and not any(char.isdigit() for char in combined):
                return combined
    return None


def _extract_date(text: str) -> str | None:
    for pattern in (ISO_DATE_RE, DMY_DATE_RE):
        match = pattern.search(text)
        if not match:
            continue
        parsed = _parse_date(match.group(0))
        if parsed:
            return parsed.isoformat()
    return None


def _parse_date(value: str) -> date | None:
    normalized = value.replace("/", "-")
    for date_format in ("%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(normalized, date_format).date()
        except ValueError:
            continue
    return None
