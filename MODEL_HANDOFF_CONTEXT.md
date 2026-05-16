# Istimara OCR Project Handoff Context

This file is written for a new model, developer, or backend teammate who needs to understand what was built, what was tested, and what still needs attention.

## Project Goal

Build a free/local OCR backend that extracts structured fields from Saudi Istimara vehicle registration documents.

The API is intended to support a Flutter app. The Flutter app sends an Istimara image or PDF to the backend, and the backend returns JSON fields such as plate number, VIN, owner name, serial number, vehicle make, model, year, color, and expiry date.

The current version uses local/free tools:

- FastAPI for the HTTP API.
- EasyOCR for Arabic and English OCR.
- OpenCV for preprocessing, cropping, resizing, and rotation handling.
- PyMuPDF for reading PDF text and rendering PDF pages.
- Deterministic Python parsing rules instead of paid OCR or AI parsing.

No paid OCR provider is currently used.

## Main API

Endpoint:

```text
POST /extract-istimara
```

Upload format:

```text
multipart/form-data
field name: file
```

Optional debug query:

```text
include_raw_text=true
```

Normal response shape:

```json
{
  "success": true,
  "data": {
    "plate_number": "1951",
    "plate_text_ar": "م ط ا",
    "plate_text_en": "Z T A",
    "serial_number": "435823700",
    "vehicle_make": "Ford",
    "vehicle_model": "Victoria",
    "model_year": "2006",
    "color": "Green",
    "vin": "2FAFP73W36X109941",
    "owner_name": "عبدالاله بن محمدبن زكريا حافظ",
    "user_name": "عبدالله بن محمدبن زكريا حافظ",
    "user_id": "1098102864",
    "expiry_date": "2029-04-18",
    "expiry_date_hijri": "1450-12-04"
  },
  "warnings": []
}
```

Important privacy note: `include_raw_text=true` is only for local debugging because raw OCR text can contain personal data.

## Important Files

- `app/main.py`: FastAPI app, health endpoint, upload endpoint.
- `app/models.py`: Pydantic response models.
- `app/services/pipeline.py`: Coordinates PDF text extraction, image OCR passes, parsing, warnings, and raw text.
- `app/services/preprocess.py`: Loads images/PDFs, crops card region, resizes large images, creates OCR variants, handles rotations.
- `app/services/ocr.py`: EasyOCR service setup and execution.
- `app/services/parser.py`: Deterministic extraction rules for VIN, plate, names, IDs, serial number, vehicle info, dates.
- `app/services/validation.py`: Upload validation, VIN validation, plate letter mappings, expiry validation.
- `tests/`: Unit/API tests for parser, pipeline, validation, and API shape.
- `README.md`: Human setup/run instructions.
- `BACKEND_INTEGRATION_STEPS.md`: Backend handoff guide.
- `FLUTTER_INTEGRATION_GUIDE.md`: Flutter client integration guide.
- `PROJECT_STEPS.md`: Checklist-style project tracker and test evidence.

## What Was Built

### FastAPI Backend

The backend accepts image/PDF uploads and returns structured JSON.

Supported file types:

- JPG
- JPEG
- PNG
- HEIC
- PDF

Upload limit:

- 10MB

Validation rejects:

- Missing filename.
- Empty file.
- Unsupported extension.
- Files over 10MB.

### OCR Pipeline

The OCR pipeline does different work depending on input type.

For PDFs:

1. Extract selectable PDF text with PyMuPDF.
2. Render PDF pages to images.
3. Run EasyOCR on rendered images.
4. Combine selectable text and OCR text.
5. Parse the combined lines.

This works well for Tawakkalna PDFs because the selectable text often contains cleaner labels and values.

For images:

1. Load image with Pillow and apply EXIF orientation.
2. Crop the likely card/document region using OpenCV.
3. Resize large screenshots before OCR.
4. Generate fast OCR variants.
5. Parse after each OCR pass and stop early if enough fields are found.
6. If extraction is weak, try stronger preprocessing.
7. If extraction is still empty, try orientation candidates.

### Image Preprocessing Enhancements

Implemented in `app/services/preprocess.py`.

Important enhancements:

- Uses `ImageOps.exif_transpose` to respect phone EXIF orientation.
- Crops the white Istimara card from dark phone screenshot backgrounds.
- Limits large image size using `IMAGE_OCR_MAX_EDGE`.
- Uses faster resize limit using `IMAGE_FAST_MAX_EDGE`.
- Produces multiple OCR variants:
  - resized color image
  - grayscale
  - sharpened
  - CLAHE contrast
  - adaptive threshold
  - Otsu threshold
- Adds orientation candidates for rotated images.
- Fixed a bug where same-size rotated candidates were accidentally deduped by shape only.
- Added upside-down landscape candidate for images rotated 180 degrees.

The important rotation fix was this idea: two rotated images can have the same width and height but different pixel content. Deduping only by shape removed valid rotation candidates. The code now hashes a sampled image signature instead.

### Parser Enhancements

Implemented mainly in `app/services/parser.py`.

The parser is deterministic and rule-based. It does not call any paid OCR or AI model.

Important parser features:

- Normalizes Arabic-Indic digits to English digits.
- Extracts valid 17-character VINs.
- Rejects VINs containing `I`, `O`, or `Q`.
- Repairs common VIN OCR mistakes:
  - Mazda leading `J` read as `I` or `1`, such as `IM7DMAW...` -> `JM7DMAW...`
  - internal `I` repaired to `1` when appropriate.
- Scores multiple VIN candidates and prefers stronger ones.
- Infers vehicle make from VIN prefixes:
  - Ford prefixes such as `2FA`
  - Mazda prefix `JM`
  - Toyota, Hyundai, Kia, Nissan, Honda prefixes.
- Infers model year from VIN year code when OCR misses the printed year.
- Extracts two-digit printed years near `سنة الصنع`.
- Extracts plate number and plate letters.
- Repairs common plate OCR mistakes:
  - `7` -> `Z`
  - `4` -> `A`
  - `8` -> `B`
  - `$` -> `S`
- Supports split plate layouts where plate number and English letters appear on different OCR lines.
- Keeps registration number separate from owner/user IDs. If no explicit registration number label exists, `registration_number` stays `null`.
- Extracts owner/user names separately.
- Extracts owner/user IDs using Saudi ID checksum validation.
- Repairs fixed-card owner/user layouts where OCR reads values before labels.
- Rejects low-signal OCR noise instead of creating fake owner names or plate fields.
- Extracts serial number near serial labels and repairs missing trailing zero in known fixed-layout cases.
- Extracts Hijri-looking expiry dates into `expiry_date_hijri` instead of pretending they are Gregorian.
- Extracts Gregorian expiry dates from Tawakkalna PDFs.
- Adds Arabic vehicle values:
  - `فورد` -> `Ford`
  - `مازدا` -> `Mazda`
  - `فيكتوريا` -> `Victoria`
  - `اخضر` -> `Green`
  - `ازرق غامق` -> `Dark Blue`
  - `CX-30` detection.

## Known Card Layouts Tested

### Tawakkalna PDF Layout

This layout has cleaner selectable text and labels such as:

- `Owner`
- `ID Number`
- `Co Owner Name`
- `Co Owner ID`
- `Car Register Number`
- `Car Serial Number`
- `Plate Number in Arabic`
- `Plate number`
- `Expire Date`
- `Expire Date in Hijri`

The PDF response became strong and usually extracts:

- Plate number.
- Plate letters.
- Serial number.
- Vehicle make.
- Vehicle model.
- Model year.
- Color.
- VIN.
- Owner name.
- User name.
- User ID.
- Expiry date.
- Hijri expiry date.

Owner ID can be extracted when the PDF text contains a valid owner identity number.

### Fixed Card Image With Owner And User

Example tested card:

- Owner: `عبدالاله بن محمدبن زكريا حافظ`
- User: `عبدالله بن محمدبن زكريا حافظ`
- User ID: `1098102864`
- VIN: `2FAFP73W36X109941`
- Plate: `1951 Z T A`
- Serial: `435823700`
- Vehicle: Ford Victoria 2006 Green

The parser had to repair:

- User name from a single OCR line `عبدالله` plus owner name tail.
- Serial number from partial OCR values such as `٤٣٥٨٢٣٧` and `٤٣٥٨٢٣٧٠`.
- VIN when multiple OCR variants produced similar values.

### Owner-Only Wafa Image Layout

Example tested card:

- Owner: `وفاء بنت علي بن سعد الصبياني`
- Owner ID: `1112658321`
- VIN: `JM7DMAW70T0322261`
- Plate: `4178 B D S`
- Serial: `456365220`
- Vehicle: Mazda CX-30 2026 Dark Blue

The card shape changes when there is no user. The parser now supports owner-only layout and does not invent a user value.

## Tests Added Or Used

Current automated test result:

```text
py -m pytest
29 passed
```

Important test files:

- `tests/test_api.py`
- `tests/test_parser.py`
- `tests/test_parser_image_layout.py`
- `tests/test_parser_layout_variants.py`
- `tests/test_parser_low_signal.py`
- `tests/test_pipeline.py`
- `tests/test_validation.py`

Important test coverage:

- VIN validation accepts valid VINs and rejects forbidden characters.
- Year parser extracts printed years.
- VIN year fallback extracts year when OCR misses printed year.
- Plate parser extracts 1-4 digit plate numbers.
- Plate parser repairs OCR letter confusion.
- Expiry date validation accepts future dates and warns on past/invalid dates.
- Upload validation rejects unsupported extensions and files over 10MB.
- API rejects missing files.
- API rejects unsupported files.
- API response shape works with mocked OCR.
- PDF selectable text is used before OCR fallback.
- Multi-pass preprocessing returns multiple variants.
- Tawakkalna PDF raw text extracts labeled fields.
- User ID is not incorrectly used as registration number.
- Fixed-card image layout repairs owner/user names and serial number.
- Low-signal rotated OCR noise does not create fake data.
- Owner-only Wafa layout extracts Mazda/CX-30 fields correctly.
- Pipeline retries rotated images only after weak first parse.
- Mazda VIN repair handles leading `J` read as `I`.

## Manual Rotated Image Tests

The user added these files:

- `WafaIstemara90.jpeg`
- `WafaIstemara180.jpeg`
- `WafaIstemara270.jpeg`

They were tested through the real FastAPI endpoint on a temporary local server:

```text
http://127.0.0.1:8003/extract-istimara
```

Results:

### WafaIstemara90.jpeg

Time:

```text
about 24 seconds
```

Returned correct fields:

```json
{
  "plate_number": "4178",
  "plate_text_ar": "ب د س",
  "plate_text_en": "B D S",
  "serial_number": "456365220",
  "vehicle_make": "Mazda",
  "vehicle_model": "CX-30",
  "model_year": "2026",
  "color": "Dark Blue",
  "vin": "JM7DMAW70T0322261",
  "owner_name": "وفاء بنت علي بن سعد الصبياني"
}
```

### WafaIstemara180.jpeg

Time:

```text
about 68 seconds
```

Returned correct fields:

```json
{
  "plate_number": "4178",
  "plate_text_ar": "ب د س",
  "plate_text_en": "B D S",
  "serial_number": "456365220",
  "vehicle_make": "Mazda",
  "vehicle_model": "CX-30",
  "model_year": "2026",
  "color": "Dark Blue",
  "vin": "JM7DMAW70T0322261",
  "owner_name": "وفاء بنت علي بن سعد الصبياني",
  "owner_id": "1112658321"
}
```

### WafaIstemara270.jpeg

Time:

```text
about 68 seconds
```

Returned correct fields:

```json
{
  "plate_number": "4178",
  "plate_text_ar": "ب د س",
  "plate_text_en": "B D S",
  "serial_number": "456365220",
  "vehicle_make": "Mazda",
  "vehicle_model": "CX-30",
  "model_year": "2026",
  "color": "Dark Blue",
  "vin": "JM7DMAW70T0322261",
  "owner_name": "وفاء بنت علي بن سعد الصبياني"
}
```

Before the rotation fix, some rotated images took about 5.5 minutes and still returned empty or weak results. After the fix, all three rotated images returned correct fields. CPU time is still not instant, but the worst case is much better.

## Performance Notes

EasyOCR on CPU is slow. This is expected.

Current speed characteristics:

- Good orientation/card crop can return in around 16-25 seconds locally.
- Hard rotated cases can still take around 68 seconds locally.
- Before fixing orientation candidate dedupe, rotated cases could take about 5.5 minutes.

Ways to improve speed without paid OCR:

- Keep image size controlled before OCR.
- Crop to the card region before OCR.
- Stop OCR early once enough key fields are extracted.
- Avoid running all rotations unless the first passes are weak.
- Run on a backend with CUDA GPU and set `EASYOCR_GPU=true`.

The user does not know whether the final backend has GPU. Therefore, the code should continue to work on CPU, but a GPU server would make OCR much faster.

## Known Limitations

- Local EasyOCR is imperfect on small Arabic/English text.
- Very blurry, dark, compressed, or heavily rotated screenshots may still fail.
- Expiry date is often missing from physical card images because it may not appear on the front side.
- PDF extraction is usually better than image extraction when Tawakkalna selectable text exists.
- The parser is rule-based, so new card layouts may require new parsing rules.
- The API should not log raw OCR text or uploaded document content because it can contain personal data.

## How To Run

Install dependencies:

```powershell
py -m pip install -r requirements.txt
```

Run the server:

```powershell
py -m uvicorn app.main:app --reload
```

Open Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Test with curl:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/extract-istimara" -H "accept: application/json" -F "file=@C:\path\to\istimara.jpeg;type=image/jpeg"
```

Debug with raw OCR:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/extract-istimara?include_raw_text=true" -H "accept: application/json" -F "file=@C:\path\to\istimara.jpeg;type=image/jpeg"
```

Run tests:

```powershell
py -m pytest
```

## Backend Integration Notes

The backend teammate can either:

1. Run this FastAPI service as a separate microservice.
2. Copy the OCR pipeline into the existing backend.

Recommended simple integration:

- Keep this FastAPI app as an internal OCR service.
- Existing backend receives the Flutter upload.
- Existing backend forwards the file to `/extract-istimara`.
- Existing backend stores only the approved structured fields.
- Existing backend should avoid storing raw OCR lines unless needed for debugging and allowed by privacy rules.

## Flutter Integration Notes

Flutter should:

1. Let the user capture or upload an Istimara image/PDF.
2. Send it as `multipart/form-data` using field name `file`.
3. Receive JSON.
4. Show extracted fields in editable form fields.
5. Let the user correct mistakes before saving.

Important UX recommendation: OCR is not perfect, so the app should not silently save extracted data without user review.

## Most Recent Recovery Work

The user accidentally pressed Ctrl+Z. After that, the code was rechecked.

Problems found:

- Some parser improvements had been undone.
- Tests failed around VIN repair, model-year fallback, serial repair, split plate parsing, user-name repair, and low-signal noise rejection.
- Rotated Wafa images were slow and some failed.

Fixes restored:

- VIN repair and VIN year fallback.
- Split English plate extraction.
- Low-signal noise rejection.
- Owner-only Wafa card support.
- User/owner name repairs.
- Saudi ID checksum validation.
- Serial trailing-zero repair.
- Mazda/CX-30/dark blue extraction.
- Rotation candidate dedupe fix.
- Upside-down landscape candidate.

Final verification after recovery:

```text
py -m pytest
29 passed
```

All three rotated Wafa image files returned correct data through the API.

