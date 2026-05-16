# Backend Handoff - Istimara OCR API

This file is for the backend developer who will integrate the OCR feature.

## Recommended Architecture

Use this project as an internal OCR microservice.

```text
Flutter app
  -> main backend
  -> Istimara OCR API
  -> main backend validates/saves confirmed data
  -> Flutter app shows editable confirmation form
```

Do not expose this OCR service directly to public mobile clients in production.

## Run Locally

```powershell
cd C:\File_Location
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

Health:

```text
GET http://127.0.0.1:8000/health
```

Expected:

```json
{"status": "ok"}
```

## Endpoint

```text
POST /extract-istimara
```

Request:

- `multipart/form-data`
- file field name: `file`
- supported: `.jpg`, `.jpeg`, `.png`, `.heic`, `.pdf`
- max size: `10MB`

Debug mode:

```text
POST /extract-istimara?include_raw_text=true
```

Use debug mode only while testing. `raw_text` can contain personal data.

## Example Response

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
  "warnings": []
}
```

## Backend Integration Example

Python:

```python
import requests


def extract_istimara(file_path: str) -> dict:
    with open(file_path, "rb") as file:
        response = requests.post(
            "http://127.0.0.1:8000/extract-istimara",
            files={"file": file},
            timeout=120,
        )
    response.raise_for_status()
    return response.json()
```

Node.js:

```js
import fs from "node:fs";
import FormData from "form-data";
import fetch from "node-fetch";

export async function extractIstimara(filePath) {
  const form = new FormData();
  form.append("file", fs.createReadStream(filePath));

  const response = await fetch("http://127.0.0.1:8000/extract-istimara", {
    method: "POST",
    body: form,
  });

  if (!response.ok) {
    throw new Error(`OCR failed: ${response.status} ${await response.text()}`);
  }

  return response.json();
}
```

## Production Notes

- Put this service behind the main backend.
- Add service-to-service authentication.
- Use HTTPS.
- Do not log uploaded files, raw OCR text, owner names, VINs, or plate numbers.
- Keep `include_raw_text=false` in production.
- Store only user-confirmed data.
- Let the frontend show an editable confirmation form.
- Treat `expiry_date_hijri` as Hijri until converted.
- Use `warnings` to decide which fields need user review.
- Because card images share a design, prefer fixed-layout and label-relative extraction over global text guessing.
- `owner_id` is returned only when an explicit owner-id value is visible. In some card images, only `user_id` is visible.

## Status Codes

- `200`: OCR ran. Check `data` and `warnings`.
- `400`: bad file, unsupported type, empty file, or unreadable file.
- `422`: missing `file` field.
- `503`: OCR engine/model initialization issue.
- `500`: unexpected backend error.
