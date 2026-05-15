# Backend Integration Steps

This is the handoff file for a backend developer who wants to integrate the Istimara OCR feature into another backend or deploy this FastAPI service as a separate microservice.

## Current Feature

The service exposes one OCR endpoint:

```text
POST /extract-istimara
```

Input:

- `multipart/form-data`
- file field name: `file`
- supported extensions: `.jpg`, `.jpeg`, `.png`, `.heic`, `.pdf`
- max size: `10MB`

Output:

```json
{
  "success": true,
  "data": {
    "plate_number": "1234",
    "plate_text_ar": "أ ب ح",
    "plate_text_en": "A B J",
    "registration_number": null,
    "serial_number": null,
    "vehicle_make": "Toyota",
    "vehicle_model": null,
    "model_year": "2023",
    "color": "White",
    "vin": "JTDBR32E720123456",
    "owner_name": null,
    "expiry_date": "2099-05-01"
  },
  "warnings": []
}
```

## Recommended Integration Option

Use this project as a small internal OCR microservice.

Flow:

```text
Flutter app
  -> existing backend
  -> Istimara OCR service /extract-istimara
  -> existing backend validates/saves confirmed data
  -> Flutter app displays editable confirmation form
```

This keeps OCR dependencies like EasyOCR, Torch, OpenCV, and PyMuPDF isolated from the main backend.

## Setup

From the project folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

Run tests:

```powershell
py -m pytest
```

Start locally:

```powershell
py -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

For access from a physical phone or another machine on the same network:

```powershell
py -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Health check:

```text
GET /health
```

Expected:

```json
{"status":"ok"}
```

## Existing Backend Call Example

Python example:

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

Node.js example:

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
    throw new Error(`OCR request failed: ${response.status} ${await response.text()}`);
  }

  return response.json();
}
```

## Production Checklist

- Put this service behind the existing backend, not directly public to mobile clients.
- Add authentication between services.
- Use HTTPS outside local development.
- Set request timeout to at least `120` seconds because OCR can be slow on first run.
- Do not log uploaded files, raw OCR text, owner names, VINs, or plate numbers.
- Delete temporary files if the integrating backend stores uploads before forwarding.
- Store only user-confirmed extracted data.
- Return `warnings` to the Flutter app so the UI can show fields that need review.

## Error Handling Contract

Expected client behavior:

- `200`: OCR ran; inspect `data` and `warnings`.
- `400`: bad upload, unsupported file, empty file, unreadable image/PDF.
- `422`: missing multipart `file` field.
- `500`: unexpected backend failure; show retry message and log only non-sensitive metadata.

## Known Limitations

- EasyOCR downloads model files on first real OCR use.
- First extraction may be slower than later requests.
- OCR confidence is not perfect, especially with glare, skew, low light, or cropped cards.
- The Flutter app should always show an editable confirmation form before saving.
- Google Vision or Azure Document Intelligence can be added later for higher production accuracy.

