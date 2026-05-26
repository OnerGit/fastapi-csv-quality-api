from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def upload_fixture(filename: str, expected_columns: str | None = None):
    data = {}
    if expected_columns is not None:
        data["expected_columns"] = expected_columns

    with (FIXTURES_DIR / filename).open("rb") as file_obj:
        return client.post(
            "/analyze",
            data=data,
            files={"file": (filename, file_obj, "text/csv")},
        )


def test_analyze_normal_csv():
    response = upload_fixture("good_sample.csv")
    data = response.json()

    assert response.status_code == 200
    assert data["filename"] == "good_sample.csv"
    assert data["row_count"] == 3
    assert data["column_count"] == 4
    assert data["column_names"] == ["id", "name", "email", "age"]
    assert data["missing_values_by_column"] == {
        "id": 0,
        "name": 0,
        "email": 0,
        "age": 0,
    }
    assert data["missing_value_ratio_by_column"] == {
        "id": 0.0,
        "name": 0.0,
        "email": 0.0,
        "age": 0.0,
    }
    assert data["duplicate_row_count"] == 0
    assert data["duplicate_row_ratio"] == 0.0
    assert data["empty_columns"] == []
    assert data["warnings"] == ["No basic data quality issues detected."]


def test_analyze_detects_missing_values():
    response = upload_fixture("bad_sample.csv")
    data = response.json()

    assert response.status_code == 200
    assert data["missing_values_by_column"]["name"] == 1
    assert data["missing_values_by_column"]["email"] == 2
    assert data["missing_value_ratio_by_column"]["email"] == 0.3333
    assert any("missing value" in warning for warning in data["warnings"])


def test_analyze_detects_duplicate_rows():
    response = upload_fixture("bad_sample.csv")
    data = response.json()

    assert response.status_code == 200
    assert data["duplicate_row_count"] == 1
    assert data["duplicate_row_ratio"] == 0.1667
    assert any("duplicate row" in warning for warning in data["warnings"])


def test_analyze_rejects_non_csv_file():
    with (FIXTURES_DIR / "not_csv.txt").open("rb") as file_obj:
        response = client.post(
            "/analyze",
            files={"file": ("not_csv.txt", file_obj, "text/plain")},
        )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_file_type"


def test_expected_columns_missing_columns_fails_schema_validation():
    response = upload_fixture(
        "good_sample.csv",
        expected_columns="id,name,email,age,signup_date",
    )
    data = response.json()

    assert response.status_code == 200
    assert data["schema_validation"]["passed"] is False
    assert data["schema_validation"]["missing_columns"] == ["signup_date"]
    assert any("expected schema" in warning for warning in data["warnings"])
