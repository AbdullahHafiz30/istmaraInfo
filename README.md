# Saudi Istimara OCR API

Free/local FastAPI service for extracting structured JSON from Saudi vehicle registration card images and PDFs.

## What This Project Does

- Accepts JPG, JPEG, PNG, HEIC, and PDF uploads.
- Extracts selectable text from PDFs first.
- Falls back to EasyOCR for image/PDF OCR.
- Uses multiple OpenCV preprocessing passes for images.
- Parses common Istimara fields into JSON.
- Returns warnings for missing or uncertain fields.

## 1. Install

Open PowerShell in this folder:

```powershell
cd C:\FileLocation
```

Create and activate a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
py -m pip install -r requirements.txt
```

EasyOCR may download model files on first real OCR use. They are stored locally in:

```text
.easyocr/
```

## 2. Run The API

Start the server:

```powershell
py -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

Expected:

```json
{"status": "ok"}
```

## 3. Test With An Image Or PDF

In Swagger:

1. Open `POST /extract-istimara`.
2. Click `Try it out`.
3. Set `include_raw_text` to `true` while testing.
4. Choose an Istimara image or PDF in the `file` field.
5. Click `Execute`.
6. Read the JSON response.

PowerShell example:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/extract-istimara?include_raw_text=true" `
  -F "file=@C:\path\to\istimara.jpg"
```

## 4. Response Shape

```json
{
  "success": true,
  "data": {
    "plate_number": "1234",
    "plate_text_ar": "أ ب ج",
    "plate_text_en": "A B J",
    "registration_number": "XXXXXXXX",
    "serial_number": "XXXXXXXX",
    "vehicle_make": "Kia",
    "vehicle_model": "Sportage",
    "model_year": "2025",
    "color": "Blue",
    "vin": "JTXXXXXXXXXXXXXXX",
    "owner_name": "Owner Name",
    "owner_id": null,
    "user_name": "User Name",
    "user_id": "1098102864",
    "expiry_date": "2029-04-18",
    "expiry_date_hijri": "1450-12-04"
  },
  "warnings": [],
  "raw_text": []
}
```

Notes:

- Missing fields are returned as `null` or omitted.
- `warnings` tells the frontend what needs review.
- `raw_text` appears only when `include_raw_text=true`.
- Do not show `raw_text` to users in production.
- For fixed-design card images, the parser uses nearby labels such as owner, user, serial number, VIN, plate, make, model, and year.
- `owner_id` may be absent if it is not visible on the card image. Do not infer it from unrelated ID text.

## 5. Run Tests

```powershell
py -m pytest
```

Expected:

```text
21 passed
```

## Important Files

- `README.md`: how to run and test locally.
- `BACKEND_INTEGRATION_STEPS.md`: handoff for backend developer.
- `FLUTTER_INTEGRATION_GUIDE.md`: handoff for Flutter developer.
- `PROJECT_STEPS.md`: implementation checklist and test evidence.
