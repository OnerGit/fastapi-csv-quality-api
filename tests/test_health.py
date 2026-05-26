from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "fastapi-csv-quality-api",
        "version": "0.1.0",
    }
