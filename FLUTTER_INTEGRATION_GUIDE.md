# Flutter Handoff - Istimara OCR API

This file is for the Flutter developer.

## How The App Should Use It

The Flutter app should upload an Istimara image/PDF to the backend, receive extracted fields, then show an editable confirmation screen.

Recommended flow:

```text
User selects/captures file
  -> Flutter sends file to backend
  -> backend calls OCR API
  -> Flutter receives extracted fields
  -> user reviews/corrects fields
  -> app saves confirmed data
```

## Backend URL

Local desktop/browser:

```text
http://127.0.0.1:8000
```

Android emulator:

```text
http://10.0.2.2:8000
```

iOS simulator:

```text
http://127.0.0.1:8000
```

Physical phone on same Wi-Fi:

```text
http://YOUR_COMPUTER_LOCAL_IP:8000
```

For a physical phone, start the API with:

```powershell
py -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Endpoint

```text
POST /extract-istimara
```

Multipart field:

```text
file
```

Supported files:

- JPG
- JPEG
- PNG
- HEIC
- PDF

Max size:

```text
10MB
```

## Flutter Packages

Add to `pubspec.yaml`:

```yaml
dependencies:
  http: ^1.2.2
  image_picker: ^1.1.2
  file_picker: ^8.1.2
```

## Dart Service Example

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

Usage:

```dart
final service = IstimaraOcrService(
  baseUrl: 'http://10.0.2.2:8000',
);

final result = await service.extractIstimara(file);
final data = result['data'] as Map<String, dynamic>;
final warnings = result['warnings'] as List<dynamic>;
```

## Response Fields

The backend may return:

- `plate_number`
- `plate_text_ar`
- `plate_text_en`
- `registration_number`
- `serial_number`
- `vehicle_make`
- `vehicle_model`
- `model_year`
- `color`
- `vin`
- `owner_name`
- `owner_id`
- `user_name`
- `user_id`
- `expiry_date`
- `expiry_date_hijri`

Any missing field should be shown as empty/editable in the confirmation screen.

## UI Rules

- Always show an editable confirmation form.
- Highlight fields mentioned in `warnings`.
- Do not save OCR data until the user confirms.
- Do not show `raw_text` in production.
- If `expiry_date_hijri` appears, show it as Hijri and do not treat it as Gregorian.
- If VIN is missing or warned, let the user type it manually.
- If `owner_id` is missing, leave it empty; do not copy `user_id` into it automatically.
