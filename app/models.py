from pydantic import BaseModel, ConfigDict


class IstimaraData(BaseModel):
    plate_number: str | None = None
    plate_text_ar: str | None = None
    plate_text_en: str | None = None
    registration_number: str | None = None
    serial_number: str | None = None
    vehicle_make: str | None = None
    vehicle_model: str | None = None
    model_year: str | None = None
    color: str | None = None
    vin: str | None = None
    owner_name: str | None = None
    expiry_date: str | None = None

    model_config = ConfigDict(extra="forbid")


class ExtractResponse(BaseModel):
    success: bool
    data: IstimaraData
    warnings: list[str] = []


class ErrorResponse(BaseModel):
    detail: str
