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
- [x] Add PDF page rendering with PyMuPDF.
- [x] Add OpenCV preprocessing.
- [x] Add EasyOCR service with Arabic and English reader.
- [x] Add deterministic field parsing.
- [x] Add VIN, date, and plate validation helpers.

## Phase 3 - API

- [x] Add `POST /extract-istimara`.
- [x] Return structured JSON fields.
- [x] Include warnings without logging raw uploaded documents or extracted personal data.
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

## Manual Smoke Test

- [ ] Install dependencies with `pip install -r requirements.txt`.
- [ ] Run `uvicorn app.main:app --reload`.
- [ ] Open `http://127.0.0.1:8000/docs`.
- [ ] Upload a sample Istimara image or PDF to `/extract-istimara`.
- [ ] Confirm the JSON response shape matches `ProjectInfo.md`.

## Test Evidence

- `py -m pytest` passed: 12 tests.
- `GET http://127.0.0.1:8000/health` returned `{"status":"ok"}`.
