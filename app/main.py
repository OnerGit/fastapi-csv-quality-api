from typing import Annotated

from fastapi import FastAPI, File, Form, UploadFile

from app.analyzer import analyze_csv_upload
from app.errors import CsvQualityApiError, csv_quality_api_error_handler
from app.models import CsvQualityReport, ErrorResponse, HealthResponse

SERVICE_NAME = "fastapi-csv-quality-api"
VERSION = "0.1.0"

app = FastAPI(
    title="FastAPI CSV Quality API",
    description="Upload a CSV file and receive a structured JSON data quality report.",
    version=VERSION,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        413: {"model": ErrorResponse, "description": "File too large"},
    },
)

app.add_exception_handler(CsvQualityApiError, csv_quality_api_error_handler)


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service=SERVICE_NAME, version=VERSION)


@app.post("/analyze", response_model=CsvQualityReport)
async def analyze_csv(
    file: Annotated[UploadFile, File(description="CSV file to analyze")],
    expected_columns: Annotated[
        str | None,
        Form(description="Optional comma-separated expected columns, for example: id,name,email"),
    ] = None,
) -> CsvQualityReport:
    return await analyze_csv_upload(file=file, expected_columns=expected_columns)
