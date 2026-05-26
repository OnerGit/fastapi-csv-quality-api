from fastapi import Request
from fastapi.responses import JSONResponse


class CsvQualityApiError(Exception):
    """Application-level error returned as a structured JSON response."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


async def csv_quality_api_error_handler(
    request: Request,
    exc: CsvQualityApiError,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )
