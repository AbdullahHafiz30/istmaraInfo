from fastapi import FastAPI, File, HTTPException, Query, UploadFile

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
    response_model_exclude_none=True,
    responses={400: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
async def extract_istimara_endpoint(
    file: UploadFile = File(...),
    include_raw_text: bool = Query(
        default=False,
        description="Local debugging only. Returns raw OCR lines and may contain personal data.",
    ),
) -> ExtractResponse:
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
            include_raw_text=include_raw_text,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
