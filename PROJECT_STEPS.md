# Istimara OCR MVP Steps

This file is the project steps counter. Check items here as implementation and verification move forward.

## Phase 1 - Project Scaffold

- [x] Read `ProjectInfo.md` and confirm MVP scope.
- [x] Create FastAPI project structure.
- [x] Add dependency list with stable version ranges.
- [x] Add `.gitignore`.
- [x] Add README setup and run instructions.
- [x] Add Flutter integration guide.
- [x] Add backend integration handoff guide.

## Phase 2 - OCR Extraction Pipeline

- [x] Add upload validation for supported file types and 10MB size limit.
- [x] Add image loading for JPG, JPEG, PNG, and HEIC.
- [x] Add selectable PDF text extraction before OCR fallback.
- [x] Add PDF page rendering with PyMuPDF.
- [x] Add OpenCV preprocessing.
- [x] Add multi-pass image preprocessing variants.
- [x] Add EasyOCR service with Arabic and English reader.
- [x] Store EasyOCR model files under project-local `.easyocr/model`.
- [x] Add deterministic field parsing.
- [x] Add VIN, date, and plate validation helpers.
- [x] Normalize Arabic-Indic digits in parsed values.
- [x] Separate Hijri-looking dates into `expiry_date_hijri`.
- [x] Infer some vehicle makes from VIN prefixes.
- [x] Prefer labeled Tawakkalna fields for plate, serial number, owner, model, color, and expiry date.
- [x] Warn when VIN-like OCR text is detected but fails validation.
- [x] Prefer stronger VIN candidates when OCR finds multiple valid VIN-like strings.
- [x] Infer two-digit model years near `سنة الصنع`.
- [x] Repair common plate OCR token confusion such as `7 T A` -> `Z T A`.
- [x] Add owner/user names and IDs as separate fields.
- [x] Recover split owner IDs and nearby serial numbers from fixed-layout OCR.
- [x] Keep registration number separate from owner/user IDs unless an explicit RN label is found.
- [x] Prefer clean repeated Tawakkalna owner/user name lines over noisy OCR title text.
- [x] Repair fixed-card image owner/user names when OCR reads the value before its Arabic label.
- [x] Repair split user IDs and serial numbers from fixed-card image OCR.
- [x] Extract owner ID from explicit PDF `ID Number / owner identity` labels.
- [x] Reject low-signal OCR noise instead of returning fake plate/name fields.
- [x] Respect image EXIF orientation before OCR.
- [x] Support owner-only Istimara card layouts with no user value.
- [x] Add Mazda CX-30, dark blue color, and shifted plate/serial repairs.
- [x] Add card-crop OCR pass for phone screenshots.
- [x] Validate Saudi-style owner/user ID candidates before accepting them.
- [x] Use VIN model-year code when OCR misses the printed year.
- [x] Add image-only rotated retry after weak OCR.
- [x] Add staged OCR so image processing can stop after enough fields are extracted.
- [x] Resize very large image inputs before OCR while keeping enough detail for Istimara text.
- [x] Add small orientation-candidate retry for rotated images.
- [x] Keep same-size rotated image candidates instead of deduping them by shape only.
- [x] Add upside-down card candidate for landscape screenshots.
- [x] Preserve raw OCR text from failed attempts for debugging.
- [x] Repair Mazda VIN OCR when leading `J` is read as `I`.

## Phase 3 - API

- [x] Add `POST /extract-istimara`.
- [x] Return structured JSON fields.
- [x] Include warnings without logging raw uploaded documents or extracted personal data.
- [x] Add optional local `include_raw_text=true` debugging output.
- [x] Add health endpoint for quick service checks.

## Phase 4 - Tests

- [x] Test VIN validation.
- [x] Test year parsing.
- [x] Test plate number parsing.
- [x] Test expiry date validation.
- [x] Test upload file validation.
- [x] Test API missing file behavior.
- [x] Test API unsupported file behavior.
- [x] Test API response shape with mocked OCR.
- [x] Test optional raw OCR text debugging output.
- [x] Test selectable PDF text extraction before OCR.
- [x] Test multi-pass preprocessing variant generation.
- [x] Test Arabic digit normalization, Hijri date separation, and VIN make fallback.
- [x] Test Tawakkalna raw OCR layout extraction.
- [x] Test invalid VIN-like image OCR warning.
- [x] Test improved image OCR parsing for best VIN, two-digit year, and plate token repair.
- [x] Test fixed-layout owner/user ID and serial extraction.
- [x] Test that Tawakkalna user ID is not used as registration number.
- [x] Test image-layout owner/user and serial repair.
- [x] Test low-signal OCR noise does not create fake card fields.
- [x] Test owner-only shifted screenshot layout.
- [x] Test VIN model-year fallback.
- [x] Test image rotation retry path.
- [x] Test leading `J` VIN repair.

## Manual Smoke Test

- [ ] Install dependencies with `pip install -r requirements.txt`.
- [ ] Run `uvicorn app.main:app --reload`.
- [ ] Open `http://127.0.0.1:8000/docs`.
- [ ] Upload a sample Istimara image or PDF to `/extract-istimara`.
- [ ] Confirm the JSON response shape matches `ProjectInfo.md`.

## Test Evidence

- `py -m pytest` passed: 29 tests.
- `py -m pytest` passed again after Ctrl+Z recovery: 29 tests.
- Real image smoke test on `http://127.0.0.1:8001/extract-istimara` returned correct plate, serial number, VIN, owner name, user name, and user ID.
- Wafa owner-only image smoke test returned correct plate, serial number, Mazda/CX-30, year, color, VIN, owner name, and owner ID.
- Rotated `WafaIstemara.jpeg` from the workspace returned plate, serial number, Mazda/CX-30, year, color, repaired VIN, and owner name in about 23.5 seconds on local CPU.
- Rotated `WafaIstemara90.jpeg`, `WafaIstemara180.jpeg`, and `WafaIstemara270.jpeg` were tested on `http://127.0.0.1:8003/extract-istimara`; all returned the correct Wafa card fields. Timings: about 24s, 68s, and 68s on local CPU.
- `GET http://127.0.0.1:8000/health` returned `{"status":"ok"}`.
- EasyOCR model warm-up completed and created `.easyocr/model/arabic.pth` and `.easyocr/model/craft_mlt_25k.pth`.
