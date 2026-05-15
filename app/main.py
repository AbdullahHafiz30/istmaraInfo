from fastapi import FastAPI, File, HTTPException, UploadFile

from app.models import ErrorResponse, ExtractResponse
from app.services.ocr import OCRService
from app.services.pipeline import extract_istimara
from app.services.validation import validate_upload

app = FastAPI(
    title="Saudi Istimara OCR Extraction API",
    description="Extract structured JSON from Saudi vehicle registration card images and PDFs.",
    version="0.1.0",
)

ocr_service = OCRService()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/extract-istimara",
    response_model=ExtractResponse,
    responses={400: {"model": ErrorResponse}},
)
async def extract_istimara_endpoint(file: UploadFile = File(...)) -> ExtractResponse:
    content = await file.read()
    validation_error = validate_upload(file.filename, content)
    if validation_error:
        raise HTTPException(status_code=400, detail=validation_error)

    try:
        return extract_istimara(
            content=content,
            filename=file.filename or "",
            content_type=file.content_type,
            ocr_service=ocr_service,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
