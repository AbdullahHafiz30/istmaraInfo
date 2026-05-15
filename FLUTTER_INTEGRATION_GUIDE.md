# Istimara OCR Backend - Flutter Integration Guide

This file is a handoff guide for connecting a Flutter app to the Saudi Istimara OCR extraction backend.

## What Was Built

The backend is a FastAPI service that accepts an Istimara image or PDF and returns structured JSON data.

Main endpoint:

```text
POST /extract-istimara
```

Supported files:

- JPG
- JPEG
- PNG
- HEIC
- PDF

Maximum file size:

```text
10MB
```

The backend uses:

- FastAPI for the HTTP API
- OpenCV for image preprocessing
- EasyOCR for Arabic and English OCR
- Regex/rule-based parsing
- Validation for VIN, expiry date, upload size, and file type

## Issues Faced During Implementation

1. `pytest` was not available from the terminal PATH.
   - Fix: used `py -m pytest` instead of `pytest`.

2. `python` command was not available directly.
   - Fix: used the Windows Python launcher: `py`.

3. Dependencies were not installed at first.
   - Fix: install them inside a virtual environment with:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

4. The first dependency install attempt failed because package downloads were blocked in the sandbox.
   - Fix: reran the install with permission to access the network.

5. Pip showed warnings about existing global package conflicts, especially around `numpy`.
   - Fix: `requirements.txt` now uses safer version ranges and pins OpenCV to a version compatible with `numpy<2`.
   - Still recommended: use `.venv` so this project does not affect global Python packages.

6. The first parser version incorrectly detected English plate letters from normal words like `Plate` and `unrelated`.
   - Fix: plate-letter parsing now trusts Arabic plate letters first, or explicit spaced English plate tokens like `A B J`.

7. Starting the server was interrupted before completion.
   - Current status: the backend is reachable at `http://127.0.0.1:8000/health` on this machine.
   - If it is not running later, start it manually using the command below.

## Backend Setup

From the project folder:

```powershell
cd C:\Users\Abdullah\Desktop\istmaraInfo
```

Create a virtual environment:

```powershell
py -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
py -m pip install -r requirements.txt
```

Run tests:

```powershell
py -m pytest
```

Expected result:

```text
12 passed
```

Start the backend:

```powershell
py -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

For a physical phone on the same Wi-Fi, start it with:

```powershell
py -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open API docs:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
GET http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

## API Request

Endpoint:

```text
POST http://127.0.0.1:8000/extract-istimara
```

Request type:

```text
multipart/form-data
```

Form field:

```text
file
```

Example with curl:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/extract-istimara" `
  -F "file=@C:\path\to\istimara.jpg"
```

## API Response

Successful response:

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

If a field is not confidently detected, it returns `null`.

If something is detected but suspicious, the backend includes messages in `warnings`.

## Flutter Integration

Add packages to `pubspec.yaml`:

```yaml
dependencies:
  http: ^1.2.2
  image_picker: ^1.1.2
  file_picker: ^8.1.2
```

Example Dart service:

```dart
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

class IstimaraOcrService {
  IstimaraOcrService({required this.baseUrl});

  final String baseUrl;

  Future<Map<String, dynamic>> extractIstimara(File file) async {
    final uri = Uri.parse('$baseUrl/extract-istimara');
    final request = http.MultipartRequest('POST', uri);

    request.files.add(
      await http.MultipartFile.fromPath('file', file.path),
    );

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw Exception('OCR request failed: ${response.statusCode} ${response.body}');
    }

    return jsonDecode(response.body) as Map<String, dynamic>;
  }
}
```

Example usage:

```dart
final service = IstimaraOcrService(
  baseUrl: 'http://127.0.0.1:8000',
);

final result = await service.extractIstimara(File('/path/to/istimara.jpg'));

final data = result['data'] as Map<String, dynamic>;
final plateNumber = data['plate_number'];
final vin = data['vin'];
```

## Important Flutter URL Notes

Use the correct backend URL depending on where the Flutter app runs.

Android emulator:

```text
http://10.0.2.2:8000
```

iOS simulator:

```text
http://127.0.0.1:8000
```

Flutter web on the same machine:

```text
http://127.0.0.1:8000
```

Physical phone:

```text
http://YOUR_COMPUTER_LOCAL_IP:8000
```

Example:

```text
http://192.168.1.20:8000
```

When testing on a physical phone:

- The phone and computer must be on the same Wi-Fi.
- Start the backend with:

```powershell
py -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- Allow Python/Uvicorn through Windows Firewall if prompted.

## Recommended Flutter Flow

1. User selects or captures an Istimara image.
2. Flutter checks file size before upload.
3. Flutter sends the file to `/extract-istimara`.
4. App shows extracted fields in an editable confirmation form.
5. User reviews and corrects any OCR mistakes.
6. App saves only the confirmed data.

## Security Notes

Istimara documents contain personal and vehicle data.

Recommended production rules:

- Use HTTPS.
- Add authentication.
- Do not log uploaded files.
- Do not log raw OCR text.
- Delete temporary files after processing.
- Let users manually confirm OCR output before saving.

## Current Test Status

The local automated test suite passed:

```text
12 passed
```

Run again with:

```powershell
py -m pytest
```
