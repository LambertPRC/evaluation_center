from fastapi.testclient import TestClient

from app.core.settings import Settings
from app.main import create_app


def unconfigured_client() -> TestClient:
    settings = Settings(
        db_user=None,
        db_password=None,
    )
    return TestClient(create_app(settings))


def test_health() -> None:
    with unconfigured_client() as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_reports_unconfigured_database() -> None:
    with unconfigured_client() as client:
        response = client.get("/api/v1/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "unavailable",
        "database": "not_configured",
    }
