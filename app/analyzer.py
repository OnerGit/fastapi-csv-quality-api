from collections import Counter
from io import BytesIO

import pandas as pd
from fastapi import UploadFile
from pandas.errors import EmptyDataError, ParserError

from app.errors import CsvQualityApiError
from app.models import ColumnNameIssues, CsvQualityReport, SchemaValidationResult

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB, intentionally small for an MVP demo.


def parse_expected_columns(expected_columns: str | None) -> list[str] | None:
    if expected_columns is None:
        return None

    columns = [column.strip() for column in expected_columns.split(",") if column.strip()]
    return columns or None


async def analyze_csv_upload(
    file: UploadFile,
    expected_columns: str | None = None,
) -> CsvQualityReport:
    filename = file.filename or "uploaded.csv"

    if not filename.lower().endswith(".csv"):
        raise CsvQualityApiError(
            code="invalid_file_type",
            message="Only .csv files are supported.",
            status_code=400,
            details={"filename": filename},
        )

    content = await file.read()

    if not content:
        raise CsvQualityApiError(
            code="empty_file",
            message="Uploaded file is empty.",
            status_code=400,
            details={"filename": filename},
        )

    if len(content) > MAX_FILE_SIZE_BYTES:
        raise CsvQualityApiError(
            code="file_too_large",
            message="Uploaded file is too large. Maximum supported size is 5 MB.",
            status_code=413,
            details={"filename": filename, "max_file_size_bytes": MAX_FILE_SIZE_BYTES},
        )

    try:
        df = pd.read_csv(BytesIO(content))
    except EmptyDataError as exc:
        raise CsvQualityApiError(
            code="empty_csv",
            message="CSV file has no readable data.",
            status_code=400,
            details={"filename": filename},
        ) from exc
    except ParserError as exc:
        raise CsvQualityApiError(
            code="csv_parse_error",
            message="CSV file could not be parsed. Please check the CSV format.",
            status_code=400,
            details={"filename": filename},
        ) from exc
    except UnicodeDecodeError as exc:
        raise CsvQualityApiError(
            code="unsupported_encoding",
            message="CSV file encoding is not supported. Please upload a UTF-8 encoded CSV.",
            status_code=400,
            details={"filename": filename},
        ) from exc

    if len(df.columns) == 0:
        raise CsvQualityApiError(
            code="no_columns",
            message="CSV file has no columns.",
            status_code=400,
            details={"filename": filename},
        )

    # Treat whitespace-only cells as missing values.
    df = df.replace(r"^\s*$", pd.NA, regex=True)

    row_count = int(len(df))
    column_names = [str(column) for column in df.columns]
    column_count = int(len(column_names))

    missing_values_by_column = {
        str(column): int(df[column].isna().sum()) for column in df.columns
    }

    missing_value_ratio_by_column = {
        str(column): round((missing_count / row_count), 4) if row_count > 0 else 0.0
        for column, missing_count in missing_values_by_column.items()
    }

    duplicate_row_count = int(df.duplicated().sum())
    duplicate_row_ratio = round((duplicate_row_count / row_count), 4) if row_count > 0 else 0.0

    empty_columns = [
        str(column)
        for column in df.columns
        if bool(df[column].isna().all())
    ]

    column_name_issues = inspect_column_names(column_names)

    expected = parse_expected_columns(expected_columns)
    schema_validation = build_schema_validation(column_names, expected) if expected else None

    warnings = build_warnings(
        row_count=row_count,
        missing_values_by_column=missing_values_by_column,
        duplicate_row_count=duplicate_row_count,
        empty_columns=empty_columns,
        column_name_issues=column_name_issues,
        schema_validation=schema_validation,
    )

    return CsvQualityReport(
        filename=filename,
        row_count=row_count,
        column_count=column_count,
        column_names=column_names,
        missing_values_by_column=missing_values_by_column,
        missing_value_ratio_by_column=missing_value_ratio_by_column,
        duplicate_row_count=duplicate_row_count,
        duplicate_row_ratio=duplicate_row_ratio,
        empty_columns=empty_columns,
        column_name_issues=column_name_issues,
        schema_validation=schema_validation,
        warnings=warnings,
    )


def inspect_column_names(column_names: list[str]) -> ColumnNameIssues:
    counts = Counter(column_names)

    duplicate_columns = sorted([column for column, count in counts.items() if count > 1])
    unnamed_columns = sorted([
        column for column in column_names if column.lower().startswith("unnamed")
    ])
    columns_with_spaces = sorted([
        column for column in column_names if column != column.strip()
    ])
    empty_column_names = sorted([
        column for column in column_names if column.strip() == ""
    ])

    return ColumnNameIssues(
        duplicate_columns=duplicate_columns,
        unnamed_columns=unnamed_columns,
        columns_with_leading_or_trailing_spaces=columns_with_spaces,
        empty_column_names=empty_column_names,
    )


def build_schema_validation(
    actual_columns: list[str],
    expected_columns: list[str],
) -> SchemaValidationResult:
    actual_set = set(actual_columns)
    expected_set = set(expected_columns)

    missing_columns = sorted(expected_set - actual_set)
    unexpected_columns = sorted(actual_set - expected_set)

    return SchemaValidationResult(
        passed=len(missing_columns) == 0,
        expected_columns=expected_columns,
        missing_columns=missing_columns,
        unexpected_columns=unexpected_columns,
    )


def build_warnings(
    row_count: int,
    missing_values_by_column: dict[str, int],
    duplicate_row_count: int,
    empty_columns: list[str],
    column_name_issues: ColumnNameIssues,
    schema_validation: SchemaValidationResult | None,
) -> list[str]:
    warnings: list[str] = []

    if row_count == 0:
        warnings.append("The CSV file has headers but no data rows.")

    total_missing_values = sum(missing_values_by_column.values())
    if total_missing_values > 0:
        warnings.append(f"The CSV file contains {total_missing_values} missing value(s).")

    if duplicate_row_count > 0:
        warnings.append(f"The CSV file contains {duplicate_row_count} duplicate row(s).")

    if empty_columns:
        warnings.append(
            "The CSV file contains empty column(s): " + ", ".join(empty_columns) + "."
        )

    if column_name_issues.duplicate_columns:
        warnings.append(
            "The CSV file contains duplicate column name(s): "
            + ", ".join(column_name_issues.duplicate_columns)
            + "."
        )

    if column_name_issues.unnamed_columns:
        warnings.append(
            "The CSV file contains unnamed column(s): "
            + ", ".join(column_name_issues.unnamed_columns)
            + "."
        )

    if column_name_issues.columns_with_leading_or_trailing_spaces:
        warnings.append(
            "The CSV file contains column name(s) with leading or trailing spaces: "
            + ", ".join(column_name_issues.columns_with_leading_or_trailing_spaces)
            + "."
        )

    if column_name_issues.empty_column_names:
        warnings.append("The CSV file contains empty column name(s).")

    if schema_validation and not schema_validation.passed:
        warnings.append(
            "The CSV file does not match the expected schema. Missing column(s): "
            + ", ".join(schema_validation.missing_columns)
            + "."
        )

    if not warnings:
        warnings.append("No basic data quality issues detected.")

    return warnings
