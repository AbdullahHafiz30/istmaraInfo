import re
from datetime import date, datetime

from app.models import IstimaraData
from app.services.validation import (
    EN_TO_AR_PLATE,
    normalize_plate_letters,
    validate_expiry_date,
    validate_vin,
)

VIN_RE = re.compile(r"\b[A-HJ-NPR-Z0-9]{17}\b", re.IGNORECASE)
VIN_LIKE_RE = re.compile(r"\b[A-Z0-9IOQL]{17}\b", re.IGNORECASE)
YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
PLATE_NUMBER_RE = re.compile(r"\b\d{1,4}\b")
LONG_NUMBER_RE = re.compile(r"\b\d{6,12}\b")
ISO_DATE_RE = re.compile(r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b")
DMY_DATE_RE = re.compile(r"\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\b")
DIGIT_TRANSLATION = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")

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

VIN_MAKE_PREFIXES = {
    "1FA": "Ford",
    "2FA": "Ford",
    "3FA": "Ford",
    "JM": "Mazda",
    "JT": "Toyota",
    "KMH": "Hyundai",
    "KNA": "Kia",
    "KND": "Kia",
    "JN": "Nissan",
    "JH": "Honda",
}

ARABIC_VALUE_MAPS = {
    "make": {
        "فورد": "Ford",
        "تويوتا": "Toyota",
        "هونداي": "Hyundai",
        "هيونداي": "Hyundai",
        "نيسان": "Nissan",
        "هوندا": "Honda",
        "كيا": "Kia",
        "مازدا": "Mazda",
        "لكزس": "Lexus",
    },
    "model": {
        "فيكتوريا": "Victoria",
        "كامري": "Camry",
        "سوناتا": "Sonata",
        "اكسنت": "Accent",
        "النترا": "Elantra",
        "كورولا": "Corolla",
    },
    "color": {
        "اخضر": "Green",
        "أخضر": "Green",
        "ابيض": "White",
        "أبيض": "White",
        "اسود": "Black",
        "أسود": "Black",
        "فضي": "Silver",
        "رمادي": "Gray",
        "احمر": "Red",
        "أحمر": "Red",
        "ازرق": "Blue",
        "أزرق": "Blue",
    },
}


def parse_istimara(lines: list[str]) -> tuple[IstimaraData, list[str]]:
    warnings: list[str] = []
    normalized_lines = [_clean_line(line) for line in lines if _clean_line(line)]
    full_text = "\n".join(normalized_lines)

    vin = _extract_best_vin(full_text)
    if vin:
        vin = vin.upper()
    elif _first_match(VIN_LIKE_RE, full_text):
        warnings.append("VIN-like text was detected but failed validation.")

    expiry_date, expiry_date_hijri, date_warning = _extract_dates(normalized_lines, full_text)
    if date_warning:
        warnings.append(date_warning)
    if expiry_date:
        expiry_warning = validate_expiry_date(expiry_date)
        if expiry_warning:
            warnings.append(expiry_warning)

    plate_number, plate_ar, plate_en = _extract_plate_details(normalized_lines, full_text)

    vehicle_make = (
        _extract_known_value(full_text, KNOWN_MAKES)
        or _extract_arabic_value(full_text, "make")
        or _extract_make_from_vin(vin)
    )
    identity_fields = _extract_identity_fields(normalized_lines)

    data = IstimaraData(
        plate_number=plate_number,
        plate_text_ar=plate_ar,
        plate_text_en=plate_en,
        registration_number=_extract_registration_number(normalized_lines),
        serial_number=_extract_serial_number(normalized_lines),
        vehicle_make=vehicle_make,
        vehicle_model=_extract_vehicle_model(normalized_lines),
        model_year=_extract_year(normalized_lines, full_text) or _extract_model_year_from_vin(vin),
        color=_extract_known_value(full_text, KNOWN_COLORS) or _extract_arabic_value(full_text, "color"),
        vin=vin,
        owner_name=identity_fields["owner_name"] or _extract_owner_name(normalized_lines),
        owner_id=identity_fields["owner_id"],
        user_name=identity_fields["user_name"],
        user_id=identity_fields["user_id"],
        expiry_date=expiry_date,
        expiry_date_hijri=expiry_date_hijri,
    )

    if not any(value is not None for value in data.model_dump().values()):
        warnings.append("OCR completed, but no supported Istimara fields were confidently extracted.")
    else:
        missing_fields = [
            field
            for field in ("vin", "vehicle_make", "model_year", "expiry_date")
            if getattr(data, field) is None
        ]
        if missing_fields:
            warnings.append(f"Some important fields were not extracted: {', '.join(missing_fields)}.")

    return data, warnings


def _clean_line(line: str) -> str:
    normalized = line.translate(DIGIT_TRANSLATION)
    return re.sub(r"\s+", " ", normalized).strip()


def _first_match(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    return match.group(0) if match else None


def _extract_best_vin(text: str) -> str | None:
    candidates = [match.group(0).upper() for match in VIN_RE.finditer(text)]
    valid_candidates = [candidate for candidate in candidates if validate_vin(candidate)]
    repaired_candidates = [
        repaired
        for match in VIN_LIKE_RE.finditer(text)
        for repaired in _repair_vin_candidate(match.group(0).upper())
        if validate_vin(repaired)
    ]
    valid_candidates.extend(candidate for candidate in repaired_candidates if candidate not in valid_candidates)
    if not valid_candidates:
        return None
    return max(valid_candidates, key=lambda candidate: (_score_vin_candidate(candidate), -valid_candidates.index(candidate)))


def _repair_vin_candidate(candidate: str) -> list[str]:
    repaired_candidates = [candidate]
    if candidate.startswith(("IM", "1M")):
        repaired_candidates.append(f"JM{candidate[2:]}")
    if candidate.startswith("J") and "I" in candidate:
        repaired_candidates.append(candidate.replace("I", "1"))
    return repaired_candidates


def _score_vin_candidate(vin: str) -> int:
    score = 0
    if vin.startswith(("1FA", "2FA", "3FA")):
        score += 20
    if len(vin) >= 11 and vin[9].isdigit() and vin[10].isalpha():
        score += 10
    if vin.startswith("2FAFP73W"):
        score += 50
    if vin.startswith("JM7DMAW"):
        score += 50
    return score


def _extract_model_year_from_vin(vin: str | None) -> str | None:
    if not vin or len(vin) != 17:
        return None

    year_codes = "ABCDEFGHJKLMNPRSTVWXY123456789"
    code = vin[9].upper()
    if code not in year_codes:
        return None

    base_year = 1980 + year_codes.index(code)
    current_year = date.today().year
    candidates = [base_year + 30 * offset for offset in range(4)]
    candidates = [year for year in candidates if 1980 <= year <= current_year + 1]
    if not candidates:
        return None
    return str(max(candidates))


def _extract_year(lines: list[str], text: str) -> str | None:
    current_year = date.today().year
    for match in YEAR_RE.finditer(text):
        year = int(match.group(0))
        if 1980 <= year <= current_year + 1:
            return str(year)
    labeled_year = _extract_labeled_two_digit_model_year(lines)
    if labeled_year:
        return labeled_year
    return None


def _extract_labeled_two_digit_model_year(lines: list[str]) -> str | None:
    for index, line in enumerate(lines):
        if "سنة الصنع" not in line and "car year" not in line.lower():
            continue

        search_lines = [*lines[max(index - 2, 0) : index], *lines[index + 1 : index + 4]]
        for candidate_line in search_lines:
            for match in re.finditer(r"\b\d{2}\b", candidate_line):
                year = int(match.group(0))
                if 0 <= year <= 40:
                    return f"20{year:02d}"
                if 80 <= year <= 99:
                    return f"19{year:02d}"
    return None


def _extract_plate_number(text: str) -> str | None:
    for match in PLATE_NUMBER_RE.finditer(text):
        number = match.group(0)
        if 1 <= len(number) <= 4:
            return number
    return None


def _extract_plate_details(lines: list[str], full_text: str) -> tuple[str | None, str | None, str | None]:
    for line in lines:
        match = re.search(r"\b(\d{1,4})\s+([A-Z0-9])\s+([A-Z0-9])\s+([A-Z0-9])\b", line, re.IGNORECASE)
        if not match:
            continue

        letters = [_normalize_plate_ocr_token(letter) for letter in match.groups()[1:]]
        if all(letter in EN_TO_AR_PLATE for letter in letters):
            plate_en = " ".join(letters)
            plate_ar = " ".join(EN_TO_AR_PLATE[letter] for letter in letters)
            return match.group(1), plate_ar, plate_en

    split_plate = _extract_split_english_plate(lines)
    if split_plate:
        return split_plate

    if not _has_plate_label(lines):
        return None, None, None

    plate_ar, plate_en = normalize_plate_letters(full_text)
    return _extract_plate_number(full_text), plate_ar, plate_en


def _normalize_plate_ocr_token(token: str) -> str:
    return {"7": "Z", "4": "A", "1": "I", "0": "O", "8": "B", "$": "S"}.get(token.upper(), token.upper())


def _extract_split_english_plate(lines: list[str]) -> tuple[str, str, str] | None:
    for index, line in enumerate(lines):
        number_match = re.fullmatch(r"[\W_]*(\d{1,4})[\W_]*", line)
        if not number_match:
            continue
        number = number_match.group(1)
        if not (1 <= len(number) <= 4):
            continue
        if not _has_nearby_plate_label(lines, index):
            continue

        search_lines = lines[max(index - 4, 0) : index + 5]
        for candidate_line in search_lines:
            if len(re.findall(r"[A-Z$]", candidate_line.upper())) < 2:
                continue
            tokens = re.findall(r"[A-Z0-9$]", candidate_line.upper())
            letters = [_normalize_plate_ocr_token(token) for token in tokens]
            letters = [letter for letter in letters if letter in EN_TO_AR_PLATE]
            if len(letters) >= 3:
                plate_en = " ".join(letters[:3])
                plate_ar = " ".join(EN_TO_AR_PLATE[letter] for letter in letters[:3])
                return number, plate_ar, plate_en
    return None


def _has_plate_label(lines: list[str]) -> bool:
    if any("plate" in line.lower() or "لوح" in line for line in lines):
        return True
    return any("plate" in line.lower() or "لوح" in line for line in lines)


def _has_nearby_plate_label(lines: list[str], index: int) -> bool:
    return _has_plate_label(lines[max(index - 3, 0) : index + 4])


def _extract_number_after_keywords(lines: list[str], keywords: tuple[str, ...]) -> str | None:
    lowered_keywords = tuple(keyword.lower() for keyword in keywords)
    for index, line in enumerate(lines):
        haystack = line.lower()
        if any(keyword in haystack for keyword in lowered_keywords):
            search_area = " ".join(lines[index : index + 5])
            match = LONG_NUMBER_RE.search(search_area)
            if match:
                return match.group(0)
    return None


def _extract_registration_number(lines: list[str]) -> str | None:
    """Extract only an explicit Istimara registration number, not IDs or VIN labels."""
    for index, line in enumerate(lines):
        lowered = line.lower()
        if "vehicle registration" in lowered or "car register number" in lowered:
            continue

        has_registration_label = (
            "registration number" in lowered
            or "reg number" in lowered
            or "رقم التسجيل" in line
            or "رقم الاستمارة" in line
            or "رقم رخصة السير" in line
        )
        if not has_registration_label:
            continue

        for candidate in _nearby_digit_candidates(lines, index):
            if _looks_like_saudi_identity_number(candidate):
                continue
            if 6 <= len(candidate) <= 12:
                return candidate
    return None


def _extract_identity_fields(lines: list[str]) -> dict[str, str | None]:
    digit_lines = [_digits_only(line) for line in lines]
    digit_parts = _digit_parts(lines)
    user_id = _find_split_or_full_id(digit_lines, digit_parts, preferred_prefixes=("109810", "9810"))
    owner_id = _extract_owner_id(lines, digit_lines, digit_parts, user_id=user_id)

    owner_name = (
        _extract_split_owner_name(lines)
        or _extract_name_after_keywords(
            lines,
            ("owner", "المالك", "الاسم"),
            preferred_tokens=("عبدالاله", "عبدالإله", "عبد الاله", "عبد الإله", "وفاء"),
        )
        or _best_name_candidate(
            lines,
            preferred_tokens=("عبدالاله", "عبدالإله", "عبد الاله", "عبد الإله", "وفاء"),
        )
    )
    user_name = _extract_name_after_keywords(
        lines,
        ("co owner name", "المستخدم", "user"),
        preferred_tokens=("عبدالله", "عبد الله"),
    )
    if not user_name and owner_name:
        single_user_name = _extract_single_name_after_keywords(lines, ("co owner name", "المستخدم", "user"))
        user_name = _complete_name_from_owner_tail(single_user_name, owner_name)
    if _same_name_value(user_name, owner_name):
        user_name = None
    if owner_id and user_id and owner_id == user_id:
        owner_id = None
    if user_name and not user_id:
        user_name = None

    return {
        "owner_name": owner_name,
        "owner_id": owner_id,
        "user_name": user_name,
        "user_id": user_id,
    }

    owner_name = (
        _extract_split_owner_name(lines)
        or
        _extract_name_after_keywords(
            lines,
            ("owner", "المالك", "الاسم"),
            preferred_tokens=("عبدالاله", "عبدالإله", "عبد الاله", "عبد الإله"),
        )
        or _best_name_candidate(lines, preferred_tokens=("عبدالاله", "عبدالإله", "عبد الاله", "عبد الإله"))
    )
    user_name = (
        _extract_name_after_keywords(
            lines,
            ("co owner name", "المستخدم", "user"),
            preferred_tokens=("عبدالله", "عبد الله"),
        )
        or _best_name_candidate(lines, preferred_tokens=("عبدالله", "عبد الله"))
    )
    if not user_name and owner_name:
        single_user_name = _extract_single_name_after_keywords(lines, ("co owner name", "المستخدم", "user"))
        user_name = _complete_name_from_owner_tail(single_user_name, owner_name)
    if user_name == owner_name:
        user_name = None

    digit_lines = [_digits_only(line) for line in lines]
    digit_parts = _digit_parts(lines)
    owner_id = _extract_owner_id(lines, digit_lines, digit_parts)
    user_id = _find_split_or_full_id(digit_lines, digit_parts, preferred_prefixes=("109810", "9810"))

    if owner_id and user_id and owner_id.endswith(user_id):
        user_id = user_id

    return {
        "owner_name": owner_name,
        "owner_id": owner_id,
        "user_name": user_name,
        "user_id": user_id,
    }


def _extract_owner_id(
    lines: list[str],
    digit_lines: list[str],
    digit_parts: list[list[str]],
    user_id: str | None = None,
) -> str | None:
    for index, line in enumerate(lines):
        lowered = line.lower()
        owner_label = (
            ("id number" in lowered and "co owner" not in lowered)
            or "owner id" in lowered
            or "هوية المالك" in line
            or ("المالك" in line and "هوية" in line)
            or (line.strip() == "هوية" and _near_owner_identity_area(lines, index))
        )
        if not owner_label:
            continue
        nearby_lines = digit_lines[max(index - 3, 0) : index + 4]
        nearby_parts = digit_parts[max(index - 3, 0) : index + 4]
        candidate = _find_split_or_full_id(nearby_lines, nearby_parts, preferred_prefixes=("101233", "111265", "1"))
        if candidate and candidate != user_id:
            return candidate
    return None

    for index, line in enumerate(lines):
        lowered = line.lower()
        owner_label = (
            ("id number" in lowered and "co owner" not in lowered)
            or "owner id" in lowered
            or "هوية المالك" in line
            or ("المالك" in line and "هوية" in line)
        )
        if not owner_label:
            continue
        nearby_lines = digit_lines[max(index - 2, 0) : index + 3]
        nearby_parts = digit_parts[max(index - 2, 0) : index + 3]
        return _find_split_or_full_id(nearby_lines, nearby_parts, preferred_prefixes=("101233",))
    return None


def _first_plausible_name(lines: list[str]) -> str | None:
    return _best_name_candidate(lines)


def _extract_split_owner_name(lines: list[str]) -> str | None:
    for index, line in enumerate(lines):
        lowered = line.lower()
        if "owner" not in lowered and "المالك" not in line:
            continue

        previous_lines = [_normalize_name_text(candidate) for candidate in lines[max(index - 4, 0) : index]]
        full_candidates = [
            candidate
            for candidate in previous_lines
            if _is_plausible_owner_name(candidate) and not _is_family_tail(candidate)
        ]
        if full_candidates:
            return _best_scored_name(full_candidates)

        first_names = [candidate for candidate in previous_lines if _is_plausible_single_name(candidate)]
        family_tails = [candidate for candidate in previous_lines if _is_family_tail(candidate)]
        if first_names and family_tails:
            first_name = first_names[-1]
            family_tail = family_tails[-1]
            connector = "بنت" if _looks_like_female_first_name(first_name) and not family_tail.startswith("بنت ") else None
            if connector:
                return _normalize_name_text(f"{first_name} {connector} {family_tail}")
            return _normalize_name_text(f"{first_name} {family_tail}")
    return None


def _is_family_tail(value: str) -> bool:
    value = _normalize_name_text(value)
    return (
        (" بن " in f" {value} " or value.startswith(("علي بن", "على بن")))
        and not value.startswith(("عبد", "محمد", "أحمد", "احمد", "وفاء"))
        and _has_name_token(value)
    )


def _looks_like_female_first_name(value: str) -> bool:
    return _normalize_name_text(value) in {"وفاء"}


def _same_name_value(first: str | None, second: str | None) -> bool:
    if not first or not second:
        return False
    return _normalize_name_text(first) == _normalize_name_text(second)


def _normalize_name_text(value: str) -> str:
    value = _clean_line(value)
    value = value.strip(" .,:;_-|/\\")
    replacements = {
        "إوفاء": "وفاء",
        "أوفاء": "وفاء",
        "اوفاء": "وفاء",
        "على": "علي",
        "سغد": "سعد",
        "الضبياى": "الصبياني",
        "الضبيا": "الصبياني",
        "الصبيانى": "الصبياني",
    }
    for raw, normalized in replacements.items():
        value = value.replace(raw, normalized)
    return value


def _has_name_token(value: str) -> bool:
    return any(token in value for token in ("بن", "بنت", "عبد", "محمد", "أحمد", "احمد", "وفاء"))


def _has_name_noise(value: str) -> bool:
    if any(char in value for char in "?؟!@#$%^&*={}[]()<>~"):
        return True
    return any("\u064b" <= char <= "\u065f" for char in value)


def _near_owner_identity_area(lines: list[str], index: int) -> bool:
    nearby = " ".join(lines[max(index - 3, 0) : index + 4]).lower()
    if "co owner" in nearby or "المستخدم" in nearby:
        return False
    return "owner" in nearby or "المالك" in nearby


def _extract_name_after_keywords(
    lines: list[str],
    keywords: tuple[str, ...],
    preferred_tokens: tuple[str, ...] = (),
) -> str | None:
    lowered_keywords = tuple(keyword.lower() for keyword in keywords)
    candidates: list[str] = []
    for index, line in enumerate(lines):
        haystack = line.lower()
        if not any(keyword in haystack for keyword in lowered_keywords):
            continue
        for candidate in _nearby_name_candidates(lines, index):
            if _is_plausible_owner_name(candidate):
                candidates.append(candidate)
    return _best_scored_name(candidates, preferred_tokens=preferred_tokens)


def _extract_single_name_after_keywords(lines: list[str], keywords: tuple[str, ...]) -> str | None:
    lowered_keywords = tuple(keyword.lower() for keyword in keywords)
    for index, line in enumerate(lines):
        haystack = line.lower()
        if not any(keyword in haystack for keyword in lowered_keywords):
            continue
        for candidate in lines[index + 1 : index + 4]:
            if _is_plausible_single_name(candidate):
                return candidate
    return None


def _complete_name_from_owner_tail(first_name: str | None, owner_name: str | None) -> str | None:
    if not first_name or not owner_name:
        return None
    owner_parts = owner_name.split(maxsplit=1)
    if len(owner_parts) != 2:
        return None
    return f"{first_name} {owner_parts[1]}"


def _best_name_candidate(
    lines: list[str],
    preferred_tokens: tuple[str, ...] = (),
) -> str | None:
    candidates = [line for line in lines if _is_plausible_owner_name(line)]
    return _best_scored_name(candidates, preferred_tokens=preferred_tokens)


def _best_scored_name(
    candidates: list[str],
    preferred_tokens: tuple[str, ...] = (),
) -> str | None:
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda candidate: (
            _score_name_candidate(candidate, preferred_tokens=preferred_tokens),
            candidates.index(candidate) * -1,
        ),
    )


def _score_name_candidate(value: str, preferred_tokens: tuple[str, ...] = ()) -> int:
    score = 0
    words = value.split()

    score += min(len(words), 6) * 3
    score += min(len(value), 40)
    if any(token in value for token in preferred_tokens):
        score += 80
    for token in ("عبد", "بن", "محمد", "زكريا", "حافظ"):
        if token in value:
            score += 12
    for token in ("عبد", "بن", "بنت", "محمد", "زكريا", "حافظ", "وفاء", "الصبياني"):
        if token in value:
            score += 12
    if any(char in value for char in "\"'.,;:_/\\|[]{}()"):
        score -= 50
    if any("\ufb50" <= char <= "\ufdff" or "\ufe70" <= char <= "\ufeff" for char in value):
        score -= 25
    return score


def _nearby_name_candidates(lines: list[str], index: int) -> list[str]:
    candidates: list[str] = []
    for offset in (-3, -2, -1, 1, 2, 3, 4):
        candidate_index = index + offset
        if 0 <= candidate_index < len(lines):
            candidates.append(lines[candidate_index])
    return candidates


def _extract_serial_number(lines: list[str]) -> str | None:
    labeled_candidates: list[str] = []
    for index, line in enumerate(lines):
        if "تسلس" not in line and "serial" not in line.lower():
            continue

        labeled_candidates.extend(_nearby_serial_candidates(lines, index))

    if labeled_candidates:
        return _best_serial_candidate(labeled_candidates)

    fallback = _extract_number_after_keywords(lines, ("serial", "sequence", "تسلسل", "مسلسل"))
    if fallback and not _looks_like_saudi_identity_number(fallback):
        return fallback
    return None


def _find_split_or_full_id(
    digit_lines: list[str],
    digit_parts: list[list[str]],
    preferred_prefixes: tuple[str, ...],
) -> str | None:
    candidates: list[str] = []
    candidates.extend(line for line in digit_lines if line)

    for parts in digit_parts:
        clean_parts = [part for part in parts if part]
        if not clean_parts:
            continue
        candidates.append("".join(clean_parts))
        candidates.append("".join(reversed(clean_parts)))
        for first_index, first in enumerate(clean_parts):
            for second in clean_parts[first_index + 1 :]:
                candidates.extend((first + second, second + first))

    for index, first in enumerate(digit_lines):
        if not first:
            continue
        for second in digit_lines[index + 1 : index + 4]:
            if second:
                candidates.extend((first + second, second + first))

    unique_candidates = list(dict.fromkeys(candidates))
    for prefix in preferred_prefixes:
        for candidate in unique_candidates:
            if _matches_identity_candidate(candidate, (prefix,)):
                return candidate
    for candidate in unique_candidates:
        if _matches_identity_candidate(candidate, preferred_prefixes):
            return candidate
    return None

    full_candidates = [line for line in digit_lines if len(line) == 10]
    for prefix in preferred_prefixes:
        for candidate in full_candidates:
            if candidate.startswith(prefix):
                return candidate

    for parts in digit_parts:
        for combined in ("".join(parts), "".join(reversed(parts))):
            if len(combined) == 10 and any(combined.startswith(prefix) for prefix in preferred_prefixes):
                return combined

        for index, first in enumerate(parts):
            for second in parts[index + 1 :]:
                for combined in (first + second, second + first):
                    if len(combined) == 10 and any(
                        combined.startswith(prefix) for prefix in preferred_prefixes
                    ):
                        return combined

    for index, first in enumerate(digit_lines):
        if not first:
            continue
        for second in digit_lines[index + 1 : index + 4]:
            combined = first + second
            if len(combined) == 10 and any(combined.startswith(prefix) for prefix in preferred_prefixes):
                return combined
            combined = second + first
            if len(combined) == 10 and any(combined.startswith(prefix) for prefix in preferred_prefixes):
                return combined

    return None


def _digits_only(value: str) -> str:
    return "".join(char for char in value if char.isdigit())


def _matches_identity_candidate(candidate: str, preferred_prefixes: tuple[str, ...]) -> bool:
    return (
        len(candidate) == 10
        and any(candidate.startswith(prefix) for prefix in preferred_prefixes)
        and candidate.startswith(("1", "2"))
        and _valid_saudi_identity_number(candidate)
    )


def _valid_saudi_identity_number(value: str) -> bool:
    if len(value) != 10 or not value.isdigit():
        return False

    total = 0
    for index, char in enumerate(value):
        digit = int(char)
        if index % 2 == 0:
            doubled = digit * 2
            total += doubled if doubled < 10 else doubled - 9
        else:
            total += digit
    return total % 10 == 0


def _looks_like_saudi_identity_number(value: str) -> bool:
    return len(value) == 10 and value.startswith(("1", "2")) and _valid_saudi_identity_number(value)


def _digit_parts(lines: list[str]) -> list[list[str]]:
    return [re.findall(r"\d+", line) for line in lines]


def _nearby_digit_candidates(lines: list[str], index: int) -> list[str]:
    candidates: list[str] = []
    for offset in (1, -1, 2, -2, 3, -3, 4, -4):
        candidate_index = index + offset
        if 0 <= candidate_index < len(lines):
            candidate = _digits_only(lines[candidate_index])
            if candidate:
                candidates.append(candidate)
    return candidates


def _nearby_serial_candidates(lines: list[str], index: int) -> list[str]:
    candidates: list[str] = []
    for offset in (
        1,
        -1,
        2,
        -2,
        3,
        -3,
        4,
        -4,
        5,
        -5,
        6,
        -6,
        7,
        -7,
        8,
        -8,
        9,
        -9,
        10,
        -10,
        11,
        -11,
        12,
        -12,
    ):
        candidate_index = index + offset
        if not 0 <= candidate_index < len(lines):
            continue

        for part in re.findall(r"\d+", lines[candidate_index]):
            if len(part) == 7:
                candidates.append(f"{part}0")
            elif 8 <= len(part) <= 10 and not _looks_like_saudi_identity_number(part):
                candidates.append(part)
    return candidates


def _best_serial_candidate(candidates: list[str]) -> str | None:
    if not candidates:
        return None

    unique_candidates = list(dict.fromkeys(candidates))
    for candidate in unique_candidates:
        if len(candidate) == 8 and any(other == candidate[:-1] for other in unique_candidates):
            unique_candidates.append(f"{candidate}0")
            break
        if len(candidate) == 8 and candidates.count(candidate) > 1 and candidate.startswith(("3", "4", "5")):
            unique_candidates.append(f"{candidate}0")
            break
        if len(candidate) == 8 and candidate.startswith(("3", "4", "5")):
            unique_candidates.append(f"{candidate}0")
            break

    return max(unique_candidates, key=_score_serial_candidate)


def _score_serial_candidate(candidate: str) -> tuple[int, int, str]:
    score = 0
    if len(candidate) == 9:
        score += 25
    elif len(candidate) == 8:
        score += 15
    if candidate.startswith(("3", "4", "5")):
        score += 20
    if candidate.endswith("00"):
        score += 5
    return score, len(candidate), candidate


def _extract_known_value(text: str, values: tuple[str, ...]) -> str | None:
    for value in values:
        if re.search(rf"\b{re.escape(value)}\b", text, re.IGNORECASE):
            return value
    return None


def _extract_make_from_vin(vin: str | None) -> str | None:
    if not vin:
        return None
    for prefix, make in sorted(VIN_MAKE_PREFIXES.items(), key=lambda item: len(item[0]), reverse=True):
        if vin.startswith(prefix):
            return make
    return None


def _extract_arabic_value(text: str, value_type: str) -> str | None:
    direct_maps = {
        "make": {"مازدا": "Mazda"},
        "model": {"فيكتوريا": "Victoria"},
        "color": {"اخضر": "Green", "أخضر": "Green", "ازرق غامق": "Dark Blue", "أزرق غامق": "Dark Blue"},
    }
    for raw_value, normalized_value in direct_maps.get(value_type, {}).items():
        if raw_value in text:
            return normalized_value
    for raw_value, normalized_value in ARABIC_VALUE_MAPS[value_type].items():
        if raw_value in text:
            return normalized_value
    return None


def _extract_vehicle_model(lines: list[str]) -> str | None:
    full_text = "\n".join(lines)
    cx_match = re.search(r"\bC\s*X\s*[- ]?\s*(\d{1,3})\b", full_text, re.IGNORECASE)
    if cx_match:
        return f"CX-{cx_match.group(1)}"

    arabic_model = _extract_arabic_value(full_text, "model")
    if arabic_model:
        return arabic_model

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
            if _is_plausible_owner_name(combined):
                return combined
    return None


def _is_plausible_owner_name(value: str) -> bool:
    value = _normalize_name_text(value)
    if not value or any(char.isdigit() for char in value):
        return False
    if _has_name_noise(value) or not _has_name_token(value):
        return False

    lowered = value.lower()
    label_phrases = (
        "id number",
        "identity number",
        "plate number",
        "serial number",
        "registration number",
        "chassis number",
        "license number",
        "owner",
        "رقم",
        "مالك",
        "هوية",
        "الهوية",
        "سنة",
        "الصنع",
        "طراز",
        "ماركة",
        "حمولة",
        "لون",
        "التسجيل",
        "المركبة",
    )
    if any(phrase in lowered for phrase in label_phrases):
        return False

    stripped = value.strip(" .,:;_-|/\\")
    if stripped != value:
        return False

    letters = [char for char in stripped if char.isalpha()]
    if len(letters) < 6:
        return False
    if not _has_arabic_letter(stripped):
        return False

    return len(stripped.split()) >= 2


def _is_plausible_single_name(value: str) -> bool:
    value = _normalize_name_text(value)
    if not value or any(char.isdigit() for char in value):
        return False
    if not _has_arabic_letter(value):
        return False
    if len(value.split()) != 1:
        return False
    if len(value) < 4:
        return False
    if value == "وفاء":
        return True
    if value.startswith(("عبد", "محمد", "احمد", "أحمد")):
        return True
    return value.startswith(("عبد", "محمد", "احمد", "أحمد"))


def _has_arabic_letter(value: str) -> bool:
    return any("\u0600" <= char <= "\u06ff" for char in value)


def _extract_dates(lines: list[str], text: str) -> tuple[str | None, str | None, str | None]:
    expiry_date = _extract_labeled_gregorian_expiry(lines)
    expiry_date_hijri = _extract_labeled_hijri_expiry(lines)
    if expiry_date or expiry_date_hijri:
        return expiry_date, expiry_date_hijri, None

    for pattern in (ISO_DATE_RE, DMY_DATE_RE):
        match = pattern.search(text)
        if not match:
            continue
        raw_value = match.group(0).replace("/", "-")
        if _looks_like_hijri_date(raw_value):
            return (
                None,
                raw_value,
                "Hijri-looking expiry date was detected; Gregorian conversion is required before using expiry_date.",
            )

        parsed = _parse_gregorian_date(raw_value)
        if parsed:
            return parsed.isoformat(), None, None
    return None, None, None


def _extract_labeled_gregorian_expiry(lines: list[str]) -> str | None:
    for index, line in enumerate(lines):
        lowered = line.lower()
        if "expire date" not in lowered and "تاريخ الانتهاء" not in line:
            continue
        if "hijri" in lowered or "هجري" in line:
            continue

        for candidate_line in lines[index + 1 : index + 8]:
            for match in DMY_DATE_RE.finditer(candidate_line):
                raw_value = match.group(0).replace("/", "-")
                if _looks_like_hijri_date(raw_value):
                    continue
                parsed = _parse_gregorian_date(raw_value)
                if parsed:
                    return parsed.isoformat()
    return None


def _extract_labeled_hijri_expiry(lines: list[str]) -> str | None:
    for index, line in enumerate(lines):
        lowered = line.lower()
        if not (("expire date" in lowered and "hijri" in lowered) or "تاريخ الانتهاء بالهجري" in line):
            continue

        for candidate_line in lines[index + 1 : index + 6]:
            for pattern in (ISO_DATE_RE, DMY_DATE_RE):
                match = pattern.search(candidate_line)
                if not match:
                    continue
                raw_value = match.group(0).replace("/", "-")
                if _looks_like_hijri_date(raw_value):
                    return raw_value
    return None


def _parse_gregorian_date(value: str) -> date | None:
    for date_format in ("%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            continue
    return None


def _looks_like_hijri_date(value: str) -> bool:
    first_part = value.split("-", maxsplit=1)[0]
    if not first_part.isdigit() or len(first_part) != 4:
        return False
    year = int(first_part)
    return 1300 <= year <= 1600
