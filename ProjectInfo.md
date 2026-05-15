# Saudi Vehicle Registration Card (Istimara) OCR Extraction System

## Overview

This document explains how to build a system that extracts information from Saudi vehicle registration cards (استمارة المركبة) using OCR (Optical Character Recognition).

The system supports:

- Photos taken from phones
- Scanned images
- Studio-quality images
- PDFs
- Screenshots from Absher

The final output is structured JSON data.

---

# Goal

Convert this:

```text
Vehicle registration image/PDF

Into this:

{
  "plate_number": "1234",
  "plate_text_ar": "أ ب ج",
  "plate_text_en": "A B J",
  "registration_number": "XXXXXXXX",
  "serial_number": "XXXXXXXX",
  "vehicle_make": "Toyota",
  "vehicle_model": "Camry",
  "model_year": "2023",
  "color": "White",
  "vin": "JTXXXXXXXXXXXXXXX",
  "owner_name": "Abdullah Hafiz",
  "expiry_date": "2027-05-01"
}
Recommended Architecture
Upload Image/PDF
        ↓
Preprocessing
(OpenCV)
        ↓
OCR Engine
(Google Vision / EasyOCR / Azure)
        ↓
Text Extraction
        ↓
Field Parsing
(Regex + Rules)
        ↓
Validation
        ↓
Structured JSON
System Components
1. File Upload Layer

Supported formats:

JPG
PNG
HEIC
PDF

Recommended limits:

Max size: 10MB
Minimum resolution: 720p
2. Image Preprocessing

Saudi Istimara cards often contain:

reflections
glare
small Arabic text
skewed angles
low lighting

Preprocessing improves OCR accuracy significantly.

Recommended preprocessing steps
Resize
image = cv2.resize(image, None, fx=2, fy=2)
Convert to grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
Noise reduction
blur = cv2.GaussianBlur(gray, (5,5), 0)
Adaptive thresholding
processed = cv2.adaptiveThreshold(
    blur,
    255,
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY,
    11,
    2
)
Perspective correction

Use contour detection to flatten the card.

3. OCR Engine Options
Option 1 — Google Vision OCR (Recommended)

Best overall choice.

Advantages:

Excellent Arabic support
Excellent English support
Handles mixed-language documents
Supports PDFs
High accuracy

Official:
https://cloud.google.com/vision/docs/ocr

Example:

from google.cloud import vision

Estimated cost:

First 1000 requests/month free
Very cheap afterward
Option 2 — Azure Document Intelligence

Good for enterprise systems.

Advantages:

Structured document extraction
Strong document AI
Enterprise-grade

Official:
https://azure.microsoft.com/en-us/products/ai-services/ai-document-intelligence

Option 3 — EasyOCR (Best Free Option)

Advantages:

Free
Local/offline
Good Arabic support

Install:

pip install easyocr

Example:

import easyocr

reader = easyocr.Reader(['ar', 'en'])
results = reader.readtext("istimara.jpg")
Option 4 — Tesseract OCR

Advantages:

Fully free
Offline

Disadvantages:

Lower Arabic accuracy
Requires more preprocessing

Install:

https://github.com/tesseract-ocr/tesseract

Example:

tesseract image.jpg output -l ara+eng
4. Field Extraction

OCR returns raw text.

The system must parse specific fields.

Common Fields in Saudi Istimara
Field	Description
Plate Number	Vehicle plate digits
Plate Letters	Arabic + English letters
Registration Number	Vehicle registration number
VIN	Chassis number
Vehicle Make	Toyota, Hyundai, etc
Model	Camry, Sonata, etc
Year	Model year
Color	Vehicle color
Owner Name	Vehicle owner
Expiry Date	Registration expiration
Example Parsing Logic
VIN Extraction

VINs are 17 characters.

vin_pattern = r'\b[A-HJ-NPR-Z0-9]{17}\b'
Year Extraction
year_pattern = r'\b(19|20)\d{2}\b'
Plate Number Extraction
plate_pattern = r'\b\d{1,4}\b'
5. Validation Layer

OCR may produce errors.

Examples:

O ↔ 0
B ↔ 8
Arabic letter confusion
Incorrect VIN characters

Validation is critical.

Recommended Validation Rules
VIN Validation
Must be 17 characters
No I/O/Q characters
Expiry Date Validation
Must be future date
Format normalization
Plate Validation
Ensure Arabic ↔ English mapping consistency
6. Final JSON Output

Example:

{
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
}
PDFs

Two PDF scenarios exist.

Scanned PDF

Needs OCR.

Workflow:

PDF
→ convert pages to images
→ OCR each page

Libraries:

pip install pdf2image
Digital PDF

Can extract text directly.

Libraries:

pdfplumber
PyMuPDF
Recommended Tech Stack
Backend
Python
FastAPI
OCR
Google Vision OCR
or
EasyOCR
Image Processing
OpenCV
Parsing
Regex
Python rules engine
Recommended API Design
Endpoint
POST /extract-istimara
Request

Multipart upload:

file=image.jpg
Response
{
  "success": true,
  "data": {
    "plate_number": "1234",
    "vehicle_make": "Toyota"
  }
}
Production Recommendations
Add Manual Review Screen

Never trust OCR 100%.

Best UX:

OCR Extraction
→ Show editable form
→ User confirms
→ Save final data

This is how banks and fintech systems work.

Security Recommendations

Vehicle cards contain personal data.

Recommendations:

Encrypt uploaded files
Delete temporary images
Use HTTPS only
Add authentication
Avoid logging raw documents
Absher Integration Notes

There is currently no publicly available developer API from Absher for vehicle registration extraction as JSON.

Enterprise integrations may exist for approved businesses/government entities.

For most applications:

OCR + Validation + Manual Confirmation

is the correct architecture.

Recommended MVP
Cheapest
EasyOCR
OpenCV
FastAPI

Estimated monthly cost:

0–50 SAR
Recommended Production Stack
Best Accuracy
Google Vision OCR
OpenCV preprocessing
Validation layer
Human confirmation UI

Estimated OCR costs remain relatively low even at scale.

Future Improvements
AI-Based Field Detection

Use object detection models:

YOLOv8
Detectron2

To locate fields before OCR.

Advantages:

Better accuracy
Faster parsing
More robust layouts
Optional Features
Real-Time Camera Scanning

Like banking apps.

Possible using:

iOS Vision Framework
ML Kit
OpenCV live detection
Final Recommendation

For a Saudi Istimara extraction system:

MVP
EasyOCR + OpenCV
Production
Google Vision OCR + Validation + Confirmation UI

This approach is scalable, affordable, and realistic for production systems.