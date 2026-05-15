# Saudi Istimara OCR MVP

FastAPI service for extracting structured JSON from Saudi vehicle registration cards using OpenCV preprocessing, EasyOCR, deterministic parsing, and validation.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

EasyOCR downloads model files on first use.

## Run

```powershell
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

## API

### `POST /extract-istimara`

Multipart form upload:

- `file`: JPG, JPEG, PNG, HEIC, or PDF
- max file size: 10MB

Response shape:

```json
{
  "success": true,
  "data": {
    "plate_number": "1234",
    "plate_text_ar": "أ ب ج",
    "plate_text_en": "A B J",
    "registration_number": "87654321",
    "serial_number": "99887766",
    "vehicle_make": "Toyota",
    "vehicle_model": "Camry",
    "model_year": "2023",
    "color": "White",
    "vin": "JTDBR32E720123456",
    "owner_name": "عبدالله حافظ",
    "expiry_date": "2027-05-01"
  },
  "warnings": []
}
```

Fields that cannot be confidently extracted are returned as `null`, with relevant warnings when validation detects issues.

## Test

```powershell
pytest
```

The API tests mock OCR so the test suite does not download EasyOCR models.
