from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., examples=["ok"])
    service: str = Field(..., examples=["fastapi-csv-quality-api"])
    version: str = Field(..., examples=["0.1.0"])


class SchemaValidationResult(BaseModel):
    passed: bool
    expected_columns: list[str]
    missing_columns: list[str]
    unexpected_columns: list[str]


class ColumnNameIssues(BaseModel):
    duplicate_columns: list[str]
    unnamed_columns: list[str]
    columns_with_leading_or_trailing_spaces: list[str]
    empty_column_names: list[str]


class CsvQualityReport(BaseModel):
    filename: str
    row_count: int
    column_count: int
    column_names: list[str]
    missing_values_by_column: dict[str, int]
    missing_value_ratio_by_column: dict[str, float]
    duplicate_row_count: int
    duplicate_row_ratio: float
    empty_columns: list[str]
    column_name_issues: ColumnNameIssues
    schema_validation: SchemaValidationResult | None = None
    warnings: list[str]


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, str | int | float | bool | list[str] | None] = {}


class ErrorResponse(BaseModel):
    error: ErrorDetail
